from cs_kit import CoreTestFunctions

from cs_config import functions


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = {
        "Prepare Solver": {
            "AGI_STUB": [{"value": 7}],
            "MARS1_targ": [{"value": True}],
            "max_nfev": [{"value": 100}]
        }
    }
    bad_adjustment = {
        "Prepare Solver": {"AGI_STUB": [{"value": 11}], "MARS1_targ": [{"value": 6}]}
    }
