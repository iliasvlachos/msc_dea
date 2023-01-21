# msc_dea

This application was developed in the context of a Master's Thesis. Full document of the thesis is available in University of Piraeus repository [Dioni](https://dione.lib.unipi.gr/xmlui/handle/unipi/15034).

dea_web is a Django project performing Data Envelopment Analysis on a set of data uploaded be the user using an Excel file.

## Run project
Copy [.env.example](dea_web/dea/.env.example) as .env and provide credentials for database.

Build containers
``docker compose up``

Run migrations
``python manage.py migrate``

## Data Envelopment Analysis

The application reads the data provided from the user constructs the linear problems for each DMU and solves them using PuLP with the CBC solver.

### Excel file
The provided file must follow a specific structure.
* First column should contain the DMU names
* First row should contain the input and output names
* There should not be any blank cells, entire rows or columns

An example file is provided. [Click here](dea_web/static/dea_file_example.xlsx) to download.

### Results

Results provided include:

* weights (variables of each input/output) for each DMU
* Efficiency scores (ratio %) for each DMU
* Lambda values
* Efficiency Projections
