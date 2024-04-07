# GAI-based FFPV Attitude Identifier

This project is a part of the bachelor degree thesis in Computer Science at IU Internationale University. The thesis is developed by David Kort under the supervision of M. Hemmer. The software is a methodical tool developed for the task of identifying the stance of municipal planning carriers on ground-mounted photovoltaic systems in Germany. It was created in partnership with [Nefino](https://www.nefino.de/).

## Project Structure

The tool is controled by streamlit from ```/src/main.py```.
An analysis is done by combining multiple sub-reports from the modules inside ```/src/data_sources/``` into a final report and classification with ```/src/reports.py```. The concept behind this is _Ensemble Learning_.

The assets have been cut down to protect the data owned by Nefino.

## Getting Started

1. Run the app in VSCode Devcontainer for an easier setup of requirements.
2. Install packages with `pip install -r non=geo-requirements.txt`. This way generating maps won't work, but this setup is easier.
2. Create a `.env` with these envs:
```
OPENAI_API_KEY=
OPENAI_ORG_ID=
GOOGLE_API_KEY=
GOOGLE_CSE_ID=
OPENAI_SMART_LLM=gpt-4-turbo-preview
OPENAI_FAST_LLM=gpt-3.5-turbo
```
3. To start the app, run `streamlit run src/main.py
4. Select Energy Types, toggle Danger Zone and click "Reset and Populate News VS". This will take a while.

## License
This project is licensed under the terms of the MIT license.
