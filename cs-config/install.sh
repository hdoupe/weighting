# bash commands for installing your package

git clone -b app https://github.com/Peter-Metz/weighting
cd weighting
git checkout app
conda install PSLmodels::taxcalc anaconda::scipy conda-forge::paramtools
pip install -e .