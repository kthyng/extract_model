from pathlib import Path

import numpy as np
import pytest
import xarray as xr

import extract_model as em


models = []

# MOM6 inputs
url = Path(__file__).parent / "test_mom6.nc"
ds = xr.open_dataset(url)
ds = ds.cf.guess_coord_axis()
da = ds["uo"]
i, j = 0, 0
Z, T = 0, None
lon1, lat1 = -166, 48
lon2, lat2 = -149.0, 56.0
lonslice = slice(None, 5)
latslice = slice(None, 5)
model_names = [None, "sea_water_x_velocity", None, None, None]
mom6 = dict(
    da=da,
    i=i,
    j=j,
    Z=Z,
    T=T,
    lon1=lon1,
    lat1=lat1,
    lon2=lon2,
    lat2=lat2,
    lonslice=lonslice,
    latslice=latslice,
    model_names=model_names,
)
models += [mom6]

# HYCOM inputs
url = Path(__file__).parent / "test_hycom.nc"
ds = xr.open_dataset(url)
da = ds["water_u"]
i, j = 0, 30
Z, T = 0, None
lon1, lat1 = -166, 48
lon2, lat2 = 149.0, -10.1
lonslice = slice(10, 15)
latslice = slice(10, 15)
model_names = [None, "eastward_sea_water_velocity", None, None, None]
hycom = dict(
    da=da,
    i=i,
    j=j,
    Z=Z,
    T=T,
    lon1=lon1,
    lat1=lat1,
    lon2=lon2,
    lat2=lat2,
    lonslice=lonslice,
    latslice=latslice,
    model_names=model_names,
)
models += [hycom]

# Second HYCOM example inputs, from Heather
url = Path(__file__).parent / "test_hycom2.nc"
ds = xr.open_dataset(url)
da = ds["u"]
j, i = 30, 0
Z, T = 0, None
lon1, lat1 = -166, 48
lon2, lat2 = -91, 29.5
lonslice = slice(10, 15)
latslice = slice(10, 15)
model_names = [None, "eastward_sea_water_velocity", None, None, None]
hycom2 = dict(
    da=da,
    i=i,
    j=j,
    Z=Z,
    T=T,
    lon1=lon1,
    lat1=lat1,
    lon2=lon2,
    lat2=lat2,
    lonslice=lonslice,
    latslice=latslice,
    model_names=model_names,
)
models += [hycom2]

# ROMS inputs
url = Path(__file__).parent / "test_roms.nc"
ds = xr.open_dataset(url)
da = ds["zeta"]
j, i = 50, 10
Z1, T = None, 0
lon1, lat1 = -166, 48
lon2, lat2 = -91, 29.5
lonslice = slice(10, 15)
latslice = slice(10, 15)
model_names = ["sea_surface_elevation", None, None, None, None]
roms = dict(
    da=da,
    i=i,
    j=j,
    Z=Z1,
    T=T,
    lon1=lon1,
    lat1=lat1,
    lon2=lon2,
    lat2=lat2,
    lonslice=lonslice,
    latslice=latslice,
    model_names=model_names,
)
models += [roms]


def test_T_interp():
    """Test interpolation in time for one model."""

    url = Path(__file__).parent / "test_roms.nc"
    ds = xr.open_dataset(url)
    da_out = em.select(da=ds["zeta"], T=0.5)
    assert np.allclose(da_out[0, 0], -0.12584045)


def test_Z_interp():
    """Test interpolation in depth for one model."""

    url = Path(__file__).parent / "test_hycom.nc"
    ds = xr.open_dataset(url)
    da_out = em.select(da=ds["water_u"], Z=1.0)
    assert np.allclose(da_out[-1, -1], -0.1365)


@pytest.mark.parametrize("model", models)
class TestModel:
    def test_grid_point_isel_Z(self, model):
        """Select and return a grid point."""

        da = model["da"]
        i, j = model["i"], model["j"]
        Z, T = model["Z"], model["T"]

        if da.cf["longitude"].ndim == 1:
            longitude = float(da.cf["X"][i])
            latitude = float(da.cf["Y"][j])
            sel = dict(longitude=longitude, latitude=latitude)

            # isel
            isel = dict(Z=Z)

            # check
            da_check = da.cf.sel(sel).cf.isel(isel)
        elif da.cf["longitude"].ndim == 2:
            longitude = float(da.cf["longitude"][j, i])
            latitude = float(da.cf["latitude"][j, i])

            isel = dict(T=T, X=i, Y=j)

            # check
            da_check = da.cf.isel(isel)

        kwargs = dict(da=da, longitude=longitude, latitude=latitude, iZ=Z, iT=T)

        da_out = em.select(**kwargs)

        assert np.allclose(da_out, da_check)

    def test_extrap_False(self, model):
        """Search for point outside domain, which should raise an assertion."""

        da = model["da"]
        lon1, lat1 = model["lon1"], model["lat1"]
        Z, T = model["Z"], model["T"]

        # sel
        longitude = lon1
        latitude = lat1

        kwargs = dict(
            da=da,
            longitude=longitude,
            latitude=latitude,
            iT=T,
            iZ=Z,
            extrap=False,
        )

        with pytest.raises(AssertionError):
            em.select(**kwargs)

    def test_extrap_True(self, model):
        """Check that a point right outside domain has
        extrapolated value of neighbor point."""

        da = model["da"]
        # varname = model["varname"]
        i, j = model["i"], model["j"]
        Z, T = model["Z"], model["T"]

        if da.cf["longitude"].ndim == 1:
            longitude_check = float(da.cf["X"][i])
            longitude = longitude_check - 0.1
            latitude = float(da.cf["Y"][j])
            sel = dict(longitude=longitude_check, latitude=latitude)

            # isel
            isel = dict(Z=Z)

            # check
            da_check = da.cf.sel(sel).cf.isel(isel)
        elif da.cf["longitude"].ndim == 2:
            longitude = float(da.cf["longitude"][j, i])
            latitude = float(da.cf["latitude"][j, i])

            isel = dict(T=T, X=i, Y=j)

            # check
            da_check = da.cf.isel(isel)

        kwargs = dict(
            da=da,
            longitude=longitude,
            latitude=latitude,
            iZ=Z,
            iT=T,
            extrap=True,
        )

        da_out = em.select(**kwargs)

        assert np.allclose(da_out, da_check, equal_nan=True)

    def test_extrap_False_extrap_val_nan(self, model):
        """Check that land point returns np.nan for extrap=False
        and extrap_val=np.nan."""

        da = model["da"]
        lon2, lat2 = model["lon2"], model["lat2"]
        Z, T = model["Z"], model["T"]

        # sel
        longitude = lon2
        latitude = lat2

        kwargs = dict(
            da=da,
            longitude=longitude,
            latitude=latitude,
            iZ=Z,
            iT=T,
            extrap=False,
            extrap_val=np.nan,
        )

        da_out = em.select(**kwargs)

        assert da_out.isnull()

    def test_locstream(self, model):

        da = model["da"]
        lonslice, latslice = model["lonslice"], model["latslice"]
        Z, T = model["Z"], model["T"]

        if da.cf["longitude"].ndim == 1:
            longitude = da.cf["X"][lonslice].values
            latitude = da.cf["Y"][latslice].values
            sel = dict(
                longitude=xr.DataArray(longitude, dims="pts"),
                latitude=xr.DataArray(latitude, dims="pts"),
            )
            isel = dict(Z=Z)

        elif da.cf["longitude"].ndim == 2:
            longitude = da.cf["longitude"].cf.isel(Y=50, X=lonslice)
            latitude = da.cf["latitude"].cf.isel(Y=50, X=lonslice)
            isel = dict(T=T)
            sel = dict(X=longitude.cf["X"], Y=longitude.cf["Y"])

        kwargs = dict(
            da=da,
            longitude=longitude,
            latitude=latitude,
            iZ=Z,
            iT=T,
            locstream=True,
        )

        da_out = em.select(**kwargs)

        # check
        da_check = da.cf.sel(sel).cf.isel(isel)

        assert np.allclose(da_out, da_check, equal_nan=True)

    def test_grid(self, model):

        da = model["da"]
        lonslice, latslice = model["lonslice"], model["latslice"]
        Z, T = model["Z"], model["T"]

        if da.cf["longitude"].ndim == 1:
            longitude = da.cf["X"][lonslice]
            latitude = da.cf["Y"][latslice]
            sel = dict(longitude=longitude, latitude=latitude)

            isel = dict(Z=Z)

            # check
            da_check = da.cf.sel(sel).cf.isel(isel)

        elif da.cf["longitude"].ndim == 2:
            longitude = da.cf["longitude"][latslice, lonslice].values
            latitude = da.cf["latitude"][latslice, lonslice].values

            isel = dict(T=T, X=lonslice, Y=latslice)

            # check
            da_check = da.cf.isel(isel)

        kwargs = dict(da=da, longitude=longitude, latitude=latitude, iZ=Z, iT=T)

        da_out = em.select(**kwargs)

        assert np.allclose(da_out, da_check)
