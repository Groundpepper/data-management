"""
NCEP Global Ocean Data Assimilation System (GODAS)
"""
import apache_beam as beam
from pangeo_forge_recipes.patterns import MergeDim, ConcatDim, FilePattern
from pangeo_forge_recipes.transforms import OpenURLWithFSSpec, OpenWithXarray, StoreToZarr, Indexed, T
variables = ['sshg', 'thflx'] 
years = [1980, 1981, 1982]

def make_full_path(variable, year):
    return f"'https://downloads.psl.noaa.gov/Datasets/godas/{variable}.{year}.nc'"
    return f'https://downloads.psl.noaa.gov/Datasets/godas/Derived/{variable}.mon.ltm.nc'
variable_merge_dim = MergeDim("variable", variables)
time_concat_dim = ConcatDim("year", years)

## preprocessing transform

class Preprocess(beam.PTransform):
    """
    Set variables to be coordinates
    """

    @staticmethod
    def _set_bnds_as_coords(item: Indexed[T]) -> Indexed[T]:
        """
        The netcdf lists some of the coordinate variables as data variables. 
        This is a fix which we want to apply to each dataset.
        """
        index, ds = item
        new_coords_vars = ['date', 'timePlot']
        ds = ds.set_coords(new_coords_vars)
        return index, ds

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        return pcoll | beam.Map(self._set_bnds_as_coords)


pattern = FilePattern(make_full_path, variable_merge_dim, time_concat_dim, file_type="netcdf4")

GODAS = (
    beam.Create(pattern.items())
    | OpenURLWithFSSpec()
    | OpenWithXarray(file_type=pattern.file_type)
    | Preprocess() # New preprocessor
    | StoreToZarr(
        target_chunks={'time':120},
        store_name="GODAS.zarr",
        combine_dims=pattern.combine_dim_keys,
    )
)