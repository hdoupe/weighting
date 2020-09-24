# bash commands for installing your package

git clone https://github.com/Peter-Metz/weighting/tree/app
cd weighting
git checkout app
conda install PSLmodels::taxcalc anaconda::scipy conda-forge::paramtools
pip install -e .