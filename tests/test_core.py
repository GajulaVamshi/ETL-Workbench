import pandas as pd
import pytest
from validators.file_validator import validate_dataframe
from profiler.data_profiler import profile_dataframe
from transformations.engine import apply_transformations

def test_empty_validation():
    with pytest.raises(ValueError): validate_dataframe(pd.DataFrame())

def test_profile():
    r=profile_dataframe(pd.DataFrame({"x":[1,1,None]}))
    assert r["missing_cells"] == 1 and r["duplicate_rows"] == 1

def test_derived_column_does_not_mutate_source():
    src=pd.DataFrame({"price":[2,3],"qty":[4,5]})
    out=apply_transformations(src,{"derived_name":"total","derived_expression":"price * qty"})
    assert out.total.tolist()==[8,15] and "total" not in src
