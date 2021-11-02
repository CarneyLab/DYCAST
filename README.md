# DYCAST

The Dynamic Continuous-Area Space-Time (DYCAST) system is a biologically based spatiotemporal model that uses georeferenced case data to identify areas at high risk for the transmission of mosquito-borne diseases such as zika, dengue, and West Nile virus (WNV).  

The original version was written by Constandinos Theophilides at the [Center for Analysis and Research of Spatial Information (CARSI)](http://carsi.hunter.cuny.edu/) at Hunter College, the City University of New York. That version was written in the Magik programming language for GE SmallWorld GIS, for use in WNV modeling (Theophilides et al 2003, 2006; Carney et al 2011).

Subsequently, the application was ported to [Python and PostGIS](https://github.com/almccon/DYCAST) by [Alan McConchie](https://github.com/almccon) for use in dengue modeling (Carney 2010).

The current version below is a continuation of that Python application. The aim is to update, streamline, and expand this application so that it supports the prediction of Zika virus. Alternatively, a **DYCAST plugin for QGIS** can be found [here](https://github.com/CarneyLab/DYCAST-QGIS), and a browser-based map interface can be found [here](https://github.com/CarneyLab/DYCAST-web). 

More information: https://www.DYCAST.org  


## Getting started

The easiest way to get started is to run DYCAST in a Docker container, available as a free download here: https://www.docker.com

On Windows, open Command Prompt (open the Windows start menu, type 'cmd' and hit enter).

On Mac OS, open Terminal. 

Then simply run: `docker run dycast/dycast --help` to see what commands are available and what parameters are required. 


## Setting up

Start with filling out any empty environment variables in the [docker-compose.yml](./docker-compose.yml) provided in this repo.
  
To start the database and run DYCAST:

- Change the directory to the folder with `docker-compose.yml` in it, e.g.: `cd Desktop/dycast`
- Run: `docker-compose up`.

This will start a cycle of 1. importing data, 2. generating risk predictions, and 3. exporting the risk.


## Parameters

**Zika min**  
spatial: 600 meters  
temporal: 38 days  
close space: 100 meters  
close time: 4 days  

**Zika max**  
spatial: 800 meters  
temporal: 38 days  
close space: 200 meters  
close time: 4 days  

**dengue min (Carney 2010)**  
spatial: 600 meters  
temporal: 28 days  
close space: 100 meters  
close time: 4 days  
threshold: 10, 5 reports  

**dengue max**  
spatial: 800 meters  
temporal: 28 days  
close space: 200 meters  
close time: 4 days  

**WNV (Carney et al 2011)**  
spatial: 2,400 meters  
temporal: 21 days  
close space: 402 meters  
close time: 3 days  
threshold: 15 reports  



## Requirements

Using Docker with the provided [docker-compose.yml](./docker-compose.yml) file will enable you to run DYCAST anywhere, on any OS. All dependencies will be installed for you and a compatible PostGIS database is set up alongside your DYCAST container. 

If you do wish to run DYCAST outside of Docker, you can use the [requirements file](./application/init/requirements.txt) to install Python package dependencies:  
`pip install -r requirements.txt`  

Please see the Docker [entrypoint file](./docker/entrypoint.sh) for pointers on how to initialize the database. 

DYCAST is built for PostgreSQL 9.6 and PostGIS 2.3.


## Data Format & Test Data

Please see the [tests data folder](./application/tests/test_data) for examples of input data. Be sure to follow this format in terms of header row and column order/count.


## Articles about the DYCAST system:

Carney, R. M., Ahearn, S. C., McConchie, A., Glaser, C., Jean, C., Barker, C., Park, B., et al. 2011. Early Warning System for West Nile Virus Risk Areas, California, USA. Emerging Infectious Diseases 17, no. 8 (August): 1445–1454. http://www.cdc.gov/eid/content/17/8/100411.htm.

Carney, R. M. 2010. GIS-based early warning system for predicting high-risk areas of dengue virus transmission, Ribeirão Preto, Brazil. Masters Thesis, Yale University. https://search.proquest.com/openview/e8950d7a3aaf656dfb676e0a86c7987e/1?pq-origsite=gscholar&cbl=18750&diss=y

Theophilides, C. N., E. S. Binkowski, S. C. Ahearn, & W. S. Paul. 2008. A Comparison of two Significance Testing Methodologies for the Knox Test. International Journal of Geoinformatics 4(3). https://bit.ly/2LCjYhs

Theophilides, C. N., S. C. Ahearn, E. S. Binkowski, W. S. Paul, & K. Gibbs. 2006. First evidence of West Nile virus amplification and relationship to human infections. International Journal of Geographical Information Science 20, no. 1: 103–115. http://www.tandfonline.com/doi/abs/10.1080/13658810500286968.

Theophilides, C. N., S. C. Ahearn, S. Grady, & M. Merlino. 2003. Identifying West Nile virus risk areas: the dynamic continuous-area space-time system. American Journal of Epidemiology 157, no. 9: 843–854. http://aje.oxfordjournals.org/content/157/9/843.short.


## Contact

Maintained by [Vincent Meijer](https://www.linkedin.com/in/vincentmeijer1/).
