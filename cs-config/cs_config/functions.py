import os
import paramtools
import pandas as pd
import numpy as np
from .helpers import retrieve_puf
from src.geoweight import Geoweight
from src.prepdata.prepdata import TAXDATA_PARAMS, PrepData
from collections import OrderedDict



def get_version():
    return "0.1.0"


def get_inputs(meta_param_dict):
    params = TAXDATA_PARAMS()
    params.specification(serializable=True)

    default_params = {"Prepare Solver": params.dump()}

    return {"meta_parameters": {}, "model_parameters": default_params}


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    params = TAXDATA_PARAMS()
    params.adjust(adjustment["Prepare Solver"], raise_errors=False)
    errors_warnings["Prepare Solver"]["errors"].update(params.errors)

    return {"errors_warnings": errors_warnings}


def run_model(meta_param_dict, adjustment):
    params = TAXDATA_PARAMS()
    adjustment = params.adjust(adjustment["Prepare Solver"])
    puf_df = retrieve_puf()

    p = PrepData(adjustment=adjustment, reweighted=puf_df)

    if "N1" not in p.targ_list:
        data = p.puf_advance_filter.drop(columns=["AGI_STUB", "s006", "pid", "N1"])
        state_targets = p.targets_wide.drop(columns=["AGI_STUB", "STATE", "N1_targ"])
    else:
        data = p.puf_advance_filter.drop(columns=["AGI_STUB", "s006", "pid"])
        state_targets = p.targets_wide.drop(columns=["AGI_STUB", "STATE"])
    iweights = p.iweights.drop_duplicates(subset=["pid"])
    weights = iweights["weight_total"]

    # test imputation
    for col in [x for x in state_targets.columns if state_targets[x].min() == 0]:
        nonzero = [x for x in state_targets[col] if x != 0]
        avg = np.mean(np.array(nonzero))
        state_targets[col][state_targets[col] == 0] = avg

    gw = Geoweight(
        weights.to_numpy(),
        data.to_numpy(),
        state_targets.to_numpy(),
        adjustment=adjustment,
    )

    # solve for state weights
    gw.geoweight()

    message = gw.result.message

    pdiff = (gw.geotargets_opt - gw.geotargets) / gw.geotargets * 100
    pdiff = pdiff.round(2)

    targs = p.targ_list
    states = p.targets_wide["STATE"]

    pdiff_df = pd.DataFrame(pdiff, index=states, columns=targs)

    weights_df = pd.DataFrame(gw.whs_opt, columns=states)

    table_pdiff = pdiff_df.to_html(classes="table table-striped table-hover")

    wh_opt = gw.whs_opt.sum(axis=1)  # sum of optimal state weights for each household
    pdiff2 = (wh_opt - gw.wh) / gw.wh * 100
    pdiff2 = pdiff2.round(2)

    message = f"Sum of squared percentage difference from target: {np.square(pdiff).sum()}. <br><br>"
    message += f"Sum of squared percentage difference between state weights and national weights: {np.square(pdiff2).sum()}."

    comp_dict = {
        "renderable": [
            {"media_type": "table", "title": "Results", "data": message},
            {
                "media_type": "table",
                "title": "Percentage difference from targets",
                "data": table_pdiff,
            },
        ],
        "downloadable": [
            {"media_type": "CSV", "title": "state_weights", "data": weights_df.to_csv()}
        ],
    }

    return comp_dict
