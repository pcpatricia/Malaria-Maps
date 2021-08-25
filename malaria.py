#!/usr/bin/env python3

# this script generates figures for each year of malaria data present in the incidence_per_1000_pop_at_risk.csv datafile
# tested with python3.7+

from geopandas.geodataframe import GeoDataFrame
import pandas as pd
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import geopandas as gpd
import geoplot as gplt
import geoplot.crs as gcrs
import os, errno
import argparse


# find countries in the malaria dataset that do not match wtih the countries in the world dataset
def check_country_names(df: pd.DataFrame, world: GeoDataFrame):
    s = df['Country']
    malaria_countries = []
    malaria_countries = s.unique()
    t = world['name']
    country_shapes = []
    country_shapes = t.unique()

    # reports which countries are not present
    for items in malaria_countries:
        if items in country_shapes:
            pass
        else:
            print(f'Info: {items} is not in country_shapes')


# copying data from malaria dataset into the appropriate records in the world dataset
def merge_malaria_columns(df: pd.DataFrame, world: GeoDataFrame):
    years = df['Year']
    years = years.unique()

    for x in world['name'].tolist():
        for year in years:
            varry = df.loc[(df['Country'] == x) & (df['Year'] == year), 'No. of cases']
            no_of_cases = 0
            if not varry.empty:
                no_of_cases = varry.values[0]
            world.loc[(world['name'] == x), year] = no_of_cases
            
    # for countries that didnt have matching names, fix names and get values         
    dict_from_csv = pd.read_csv(os.path.join('data','correct_names.csv'), header=None, index_col=0, squeeze=True, escapechar='\\', encoding='utf-8').to_dict()
    for correct, incorrect in dict_from_csv.items():
        for year in years:
            world.loc[(world['name'] == correct), year] = df.loc[(df['Country'] == incorrect) & (df['Year'] == year), 'No. of cases'].values[0]

# generarates a single image for year of malaria for specified continent and world data
def generate_png_for_year(merged_world_data: GeoDataFrame, continent: str, year: int, vmin, vmax, figsize, dpi):

    if continent is 'World':
        data = merged_world_data
    else:
        data = merged_world_data.query('continent == "{0}"'.format(continent))

    print('Generating figure for ' + continent + ' ' + str(year))
    cases_per_country = data[year]
    ax = data.plot(color="grey", figsize=figsize)
    # position the annotation to the bottom left
    year_font_size = 36 * (figsize[0] / 16)
    plt.annotate(year, xy=(0.2, .4), xycoords='figure fraction', 
                 horizontalalignment='left', verticalalignment='top', fontsize=year_font_size)
    current_cmap = cm.get_cmap('rainbow').copy()
    current_cmap.set_under(color='gray')
    
    gplt.choropleth(data, ax=ax, hue=cases_per_country, scheme=None, 
                       cmap=current_cmap, legend=True, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    
    title_font_size = 30 * (figsize[0] / 16)
    ax.set_title("Number of cases of Malaria per year (per 1000)", fontsize=title_font_size)

    # save fig
    filepath = os.path.join('output',str(year)+'_'+continent+'_rainbow_malaria.png')
    plt.savefig(filepath, dpi=dpi)

    # free figure memory
    plt.close()


##################################################

parser = argparse.ArgumentParser(description='Make a figure of malaria cases on a continent or the world for the years in the dataset')
parser.add_argument('--geography', default='World', type=str,
                    help='Africa, Asia, Europe, South America, North America, or World (default is World)')
parser.add_argument('--dpi', default=150, type=int,
                    help='DPI value')

args = parser.parse_args()

# VALIDATE INPUT
ALLOWED_GEO = {'Africa', 'Asia', 'Europe', 'South America', 'North America', 'World'}
if args.geography not in ALLOWED_GEO:
    print('--geography must be: Africa, Asia, Europe, South America, North America, or World')
    exit(1)

if args.dpi < 75 or args.dpi > 600:
    print('--dpi must be in range 75 - 600')
    exit(1)

# read in polygon dataframe for world atlas
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# read in the malaria dataset
df = pd.read_csv(os.path.join('data','incidence_per_1000_pop_at_risk.csv'))

# create columns on the world dataframe for each year listed in the year column of the malaria table and filled with NaN values
years = df['Year']
years = years.unique()
for year in years:
    world[years] = np.nan

check_country_names(df, world)

merge_malaria_columns(df, world)

# find min and max values for later use in plot
vmin = 0.00001 
vmax = round(df['No. of cases'].max(axis=0), -2)
FIGSIZE = (16,8)

# create output directory for images
try:
    os.makedirs('output')
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

for year in years:
    generate_png_for_year(world, args.geography, year, vmin, vmax, FIGSIZE, args.dpi)

print('Done')