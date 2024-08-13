# grl_amod_with_pt
This repository contains the codebase of my master's thesis. It is about the use of graph-based reinforcement learning for integrating autonomous on-demand services with regular public transportation.

## Run the application
To start the app, run the `main.py` file in the root directory. Based on your local device, this can be achieved via `py main.py` or `python3 main.py`. After startup, install all required packages to your local python installation with pip. After the application started, a menu will be displayed into your console. The first option will start the graph reinforcement learning algorithm either for the whole 21 day simulation period or a single day. The other three options are only important, when you want to  recreate some static data or for analysis purposes.

## Configure the application
Configuration can be done in the `params/program_params.py`. All parameters used in the masters thesis can be configured here. Initially shown is the standard parameter set.

## Parallelization
To activate parallelization capabilities you can configure the parameters in the `params/concurrency_params.py`. The amount of worker processes can be configured with the `AMOUNT_OF_PROCESSES` parameter and the parallelization of the three stages can be activated with the corresponding flags. 

**Important**: The parallelization is only tested in an Ubuntu 22.04.2 LTS environment. It is known to fail in an Windows 11 environment. For safe execution outside of an linux environment, consider using Docker.