#!/bin/bash

echo Setup Brew and Python
bash_path=" ~/.bash_profile"
if ! which -s brew; then
  # Install Homebrew
  echo Setting up Homebrew
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
  echo "PATH='/usr/local/bin:$PATH'" >>$bash_path
  source $bash_path
else
  brew update && brew upgrade
fi
# Python setup is missing

echo Activate the virtual environment
has_venv=$([[ $VIRTUAL_ENV == "" ]])
if [[ $has_venv == 0 ]]; then
  # Check if the venv exists. If not end the program with a warning
  echo Activating Virtual Environment
  source .venv/bin/activate
fi

echo Setup environment variables
if [[ $ENV_FLAG == "" ]]; then
  cat .env >>$bash_path
fi

echo Starting the application
main_path=src/multibajajmgt/main.py
python $main_path
ret=$?
if [ $ret -ne 0 ]; then
  sed -i '' "s/price_dpmc_service.export_prices()/# price_dpmc_service.export_prices()/g" $main_path
  while :; do
    echo Restarting the application
    python $main_path
    ret=$?
    [ $ret -ne 0 ] || break
  done
fi

echo Resetting changes to the main file
sed -i '' "s/# price_dpmc_service.export_prices()/price_dpmc_service.export_prices()/g" $main_path
