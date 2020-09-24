import os
import paramtools
from .helpers import retrieve_puf
from src.geoweight import Geoweight
from src.prepdata.prepdata import TAXDATA_PARAMS, PrepData
from collections import OrderedDict


AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")


def get_version():
    return "0.0.0"


def get_inputs(meta_param_dict):
    params = TAXDATA_PARAMS()
    params.specification(serializable=True)

    filtered_params = OrderedDict()
    for k, v in params.dump().items():
        if k == "schema":
            filtered_params[k] = v

    default_params = {"Choose Targets": filtered_params}

    return {"meta_parameters": {}, "model_parameters": default_params}


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    params = TAXDATA_PARAMS()
    params.adjust(adjustment["Choose Targets"], raise_errors=False)
    errors_warnings["Choose Targets"]["errors"].update(params.errors)

    return {"errors_warnings": errors_warnings}


def run_model(meta_param_dict, adjustment):
    params = TAXDATA_PARAMS()
    adjustment = params.adjust(adjustment["Choose Targets"])
    puf_df = retrieve_puf(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

    p = PrepData(adjustment=adjustment, reweighted=puf_df)

    if "N1" not in data.targ_list:
        data = p.puf_advance_filter.drop(columns=['AGI_STUB','s006','pid','N1'])
        state_targets = p.targets_wide.drop(columns=['AGI_STUB','STATE','N1_targ'])
    else:
        data = p.puf_advance_filter.drop(columns=['AGI_STUB','s006','pid'])
        state_targets = p.targets_wide.drop(columns=['AGI_STUB','STATE'])
    iweights = p.iweights.drop_duplicates(subset=['pid'])
    weights = iweights['weight_total']

    # test imputation
    for col in [x for x in state_targets.columns if state_targets[x].min() == 0]:
        nonzero = [x for x in state_targets[col] if x != 0]
        avg = np.mean(np.array(nonzero))
        state_targets[col][state_targets[col] == 0] = avg

    gw = Geoweight(weights.to_numpy(), data.to_numpy(), state_targets.to_numpy())

    # solve for state weights
    gw.geoweight()

    message = gw.result.message

    pdiff = (gw.geotargets_opt - gw.geotargets) / gw.geotargets * 100

    targs = p.targ_list
    states = p.targets_wide['STATE']

    pdiff_df = pd.DataFrame(pdiff, index=states, columns=targs)

    weights_df = pd.DataFrame(gw.whs_opt, columns=states)

    table_pdiff = pdiff_df.to_html(classes="table table-striped table-hover")

    wh_opt = gw.whs_opt.sum(axis=1) # sum of optimal state weights for each household
    pdiff2 = (wh_opt - gw.wh) / gw.wh * 100

    message = f"Squared % diff from target: {np.square(pdiff).sum()} \n"
    message += f"Squared '%' diff between sum of state weights and national weights: {np.square(pdiff2).sum()} \n"
    message += f"'%' diff between sum of state weights and national weights: {pdiff2}"

    comp_dict = {
        "renderable": [
            {
                "media_type": "table",
                "title": "Results",
                "data": message,
            },
            {
                "media_type": "table",
                "title": "Percentage difference from targets",
                "data": table_pdiff,
            },
        ],
        "downloadable": [
            {
                "media_type": "CSV",
                "title": "state_weights",
                "data": weights_df.to_csv(),
            }
        ],
    }

    return comp_dict
