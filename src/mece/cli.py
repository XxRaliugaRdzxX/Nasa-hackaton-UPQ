"""Interfaz de línea de comandos: punto de entrada único para personas y para el cron.

mece check-config      valida config/*.yaml
mece check-access      prueba credenciales y acceso a cada producto NASA
mece regions build     construye los polígonos de regiones y la figura de control
"""

from __future__ import annotations

import logging

import typer

from mece.config import ConfigError, get_settings

app = typer.Typer(
    help="Marine Ecosystem Change Explorer", no_args_is_help=True, add_completion=False
)
regions_app = typer.Typer(help="Regiones de estudio", no_args_is_help=True)
app.add_typer(regions_app, name="regions")
pipeline_app = typer.Typer(help="Preparación de datos (worker)", no_args_is_help=True)
app.add_typer(pipeline_app, name="pipeline")


@app.callback()
def _main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Mostrar logs detallados"),
) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _settings():
    try:
        return get_settings()
    except ConfigError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(2) from exc


@app.command("check-config")
def check_config() -> None:
    """Valida los archivos de configuración."""
    s = _settings()
    typer.secho(
        f"OK · {len(s.products)} productos · {len(s.regions)} regiones · datos en {s.data_dir}",
        fg="green",
    )
    for key, p in s.products.items():
        typer.echo(f"  {key:22s} {p.variable:13s} {p.role:10s} {p.short_name} v{p.version}")


@app.command("check-access")
def check_access() -> None:
    """Verifica credenciales de Earthdata y acceso real a cada producto (no imprime secretos)."""
    from mece.acquisition.auth import EarthdataAuthError
    from mece.acquisition.auth import check_access as _check

    s = _settings()
    try:
        results = _check(s)
    except EarthdataAuthError as exc:
        typer.secho(str(exc), fg="red", err=True)
        raise typer.Exit(1) from exc
    typer.secho("Login Earthdata: OK", fg="green")
    for r in results:
        typer.secho(
            f"  {'OK ' if r.ok else 'ERR'} {r.daac:9s} {r.product_key:22s} {r.detail}",
            fg="green" if r.ok else "red",
        )
    if not all(r.ok for r in results):
        raise typer.Exit(1)


@regions_app.command("build")
def regions_build(
    download: bool = typer.Option(True, help="Descargar fuentes que falten"),
    force_download: bool = typer.Option(False, help="Volver a descargar todas las fuentes"),
    figure: bool = typer.Option(True, help="Generar docs/figuras/regiones_control.png"),
) -> None:
    """Construye los GeoJSON de regiones en data/spatial/regions/."""
    from mece.geospatial import build_regions as br

    s = _settings()
    if download:
        br.download_sources(s.ancillary_dir, force=force_download)
    regions = br.build_regions(s)
    paths = br.write_regions(regions, s.regions_dir)
    typer.secho(f"{len(paths)} polígonos escritos en {s.regions_dir}", fg="green")
    typer.echo(br.summary_table(regions).to_string(index=False))
    if figure:
        fig = br.plot_control(regions, s, s.root / "docs" / "figuras" / "regiones_control.png")
        typer.echo(f"Figura de control: {fig}")


@pipeline_app.command("fetch")
def pipeline_fetch(
    dataset: str = typer.Option(..., help="chl | sst"),
    start: str = typer.Option(None, help="YYYY-MM (por defecto, inicio del producto)"),
    end: str = typer.Option(None, help="YYYY-MM (por defecto, último mes disponible)"),
) -> None:
    """Llena los almacenes regionales con un dataset (solo descarga lo que falta)."""
    from mece import pipeline

    typer.echo(pipeline.fetch(dataset, start, end))


@pipeline_app.command("globe")
def pipeline_globe() -> None:
    """Textura de SST global y costas para el globo 3D."""
    from mece import pipeline

    typer.echo(pipeline.globe_texture())
    typer.echo(pipeline.coastline_110m())


@pipeline_app.command("precompute")
def pipeline_precompute(
    case: list[str] = typer.Option(None, help="IDs de caso (todos si se omite)"),
) -> None:
    """Precalcula mapas de tendencia de cada caso de estudio."""
    from mece import pipeline

    for k, v in pipeline.precompute(case).items():
        typer.echo(f"  {k:32s} {v}")


@pipeline_app.command("bootstrap")
def pipeline_bootstrap() -> None:
    """Preparación completa: globo, clorofila, SST y precálculo."""
    from mece import pipeline

    pipeline.coastline_110m()
    pipeline.globe_texture()
    pipeline.fetch("chl")
    pipeline.fetch("sst")
    pipeline.precompute()


if __name__ == "__main__":
    app()
