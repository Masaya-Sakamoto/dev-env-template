import click
from pathlib import Path

from plateau_rt.application.build_scene import SceneBuilder
from plateau_rt.adapters.sionna.simulator import SionnaSimulator

@click.group()
def cli():
    """PLATEAU CityJSON to Sionna-RT Dataset Generator"""
    pass

@cli.command("build")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output_dir", type=click.Path(file_okay=False, path_type=Path))
def build_scene(input_file: Path, output_dir: Path):
    """
    Step 1: CityJSONからSionna-RT用シーン(PLY/XML)とマニフェストを生成します。
    """
    click.echo(f"Building scene from {input_file} into {output_dir}...")
    builder = SceneBuilder(input_file, output_dir)
    xml_path = builder.run()
    click.echo(click.style(f"Success! Scene XML generated at: {xml_path}", fg="green"))

@cli.command("simulate")
@click.argument("xml_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("manifest_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output_dir", type=click.Path(file_okay=False, path_type=Path))
def simulate_coverage(xml_file: Path, manifest_file: Path, output_dir: Path):
    """
    Step 2: 生成されたXMLとマニフェストを用いて電波カバレッジマップを計算します。
    """
    click.echo(f"Running simulation for {xml_file}...")
    
    # 出力先ディレクトリの確保
    output_dir.mkdir(parents=True, exist_ok=True)
    
    simulator = SionnaSimulator(xml_file, manifest_file)
    result_path = simulator.run_coverage_simulation(output_dir)
    click.echo(click.style(f"Success! Coverage map generated at: {result_path}", fg="green"))

@cli.command("run-all")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("output_dir", type=click.Path(file_okay=False, path_type=Path))
def run_all(input_file: Path, output_dir: Path):
    """
    一気貫通: CityJSONのパースから電波シミュレーションまでを全自動で実行します。
    """
    click.echo(click.style("=== Starting End-to-End Pipeline ===", fg="cyan"))
    
    # 1. シーン構築
    builder = SceneBuilder(input_file, output_dir)
    xml_path = builder.run()
    manifest_path = output_dir / "manifest.json"
    
    # 2. シミュレーション実行
    click.echo(click.style("=== Proceeding to Simulation ===", fg="cyan"))
    simulator = SionnaSimulator(xml_path, manifest_path)
    result_path = simulator.run_coverage_simulation(output_dir)
    
    click.echo(click.style(f"=== Pipeline Finished! Result: {result_path} ===", fg="green", bold=True))

if __name__ == "__main__":
    cli()