import argparse
import os
import re
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import csv
import xml.etree.ElementTree as ET


## check_path():
## Check that a directory exists and create it if it doesn't

def check_path(path):
    """
    Check that a directory exists and create it if it doesn't
    """    
    if not os.path.exists(path):
        try:
            os.makedirs(path)            
        except OSError as e:
            print(f"Error creating directory: {e}")
            sys.exit(1)

def qc_report(data):
    """
    Print a warning if any of the required data fields are missing
    Required fields are title, description, copyright, url, short_name, pub_date
    Return: error count (int)
    """
    error_count = 0
    required_fields = ['title', 'description', 'copyright', 'url', 'short_name', 'pub_date']
    for field in required_fields:
        if not data.get(field):
            print(f"Warning: The required field '{field}' is missing or empty.")
            error_count += 1
    return error_count


def process_non_breaking_space(line, use_comma=True):
    """
    Remove non-breaking space characters from the confluence line
    If replacing with  characters, set use_html = True
    Return: line with eol removed
    """
    repl_str = ' '
    if use_comma:
        repl_str = ',' 
    # Replace &nbsp; character code with repl_str
    cleaned_line = re.sub(r'\xa0', repl_str, line)
    # Replace ,, with a single comma
    cleaned_line = re.sub(r'\,\,', ', ', cleaned_line)
    # Fix those pesky word boundary commas
    cleaned_line = re.sub(r'(?<=\w),(?=\w)', ', ', cleaned_line) 
    return cleaned_line

def cs_df_to_xml(df, xml_file):
    """
    Convert the dataframe in parameter 1 to xml transforming the confluence form Data element and Sub data elements
    to CodeSystem elements.
    Output the CodeSystem to an XML file name from parameter 2
    """ 
    cs = ET.Element('CodeSystem', xmlns="http://hl7.org/fhir")
    data = {}
    src_contact = {}    
    for _, row in df.iterrows():        
        if pd.notna(row[0]) and pd.notna(row[1]):
            src_ele = row[0].replace(" ", "") + "." + row[1].replace(" ", "")
        elif pd.notna(row[0]):
            src_ele = row[0].replace(" ", "")
        else:
            continue
        # Populate the element variables
        if src_ele == 'CodeSystemNames.Formalnameofthecodesystem' and pd.notna(row[2]):
            data['title'] = row[2]
        if src_ele == 'CodeSystemTechnicalIdentifiers.HTA-endorsedURI' and pd.notna(row[2]):
            data['url'] = row[2]
        if src_ele == 'CodeSystemNames.Shortnameofthecodesystem' and pd.notna(row[2]):
            data['short_name'] = row[2]    
        if src_ele == 'CodeSystemOwner.Name' and pd.notna(row[2]):
            src_contact['name'] = process_non_breaking_space(row[2],use_comma=True)
        if src_ele == 'CodeSystemOwner.Address' and pd.notna(row[2]):
            src_contact['address'] = process_non_breaking_space(row[2])
        if src_ele == 'CodeSystemOwner.Website' and pd.notna(row[2]):
            src_contact['website'] = row[2]
            src_contact['system'] = 'url'
        if src_ele == 'CodeSystemInformation.Notes' and pd.notna(row[2]):
            data['description'] = process_non_breaking_space(row[2].replace('"',''),use_comma=False)
        if src_ele == 'CodeSystemCopyright,IntellectualPropertyandLicensing.CopyrightStatement' and pd.notna(row[2]):
            data['copyright'] = process_non_breaking_space(row[2].replace('"',''), use_comma=False)
        if src_ele == 'Informationcurrentasat(date)':
            data['pub_date'] = row[2]
    # Build the XML: Add elements to the cs element
    ET.SubElement(cs, 'id').set('value', data.get('short_name',''))    
    ET.SubElement(cs, 'url').set('value', data.get('url',''))
    ET.SubElement(cs, 'version').set('value', '1.0.0')
    ET.SubElement(cs, 'name').set('value', data.get('short_name',''))   
    ET.SubElement(cs, 'title').set('value', data.get('title',''))
    ET.SubElement(cs, 'status').set('value', 'active')
    ET.SubElement(cs, 'experimental').set('value', 'false')
    ET.SubElement(cs, 'date').set('value', data.get('pub_date',''))
    ET.SubElement(cs, 'publisher').set('value',src_contact.get('name',''))
    # Set up nested contact element
    contact = ET.SubElement(cs, 'contact')
    telecom = ET.SubElement(contact,'telecom')
    ET.SubElement(telecom, 'system').set('value', src_contact.get('system',''))
    ET.SubElement(telecom, 'value').set('value', src_contact.get('website',''))
    data['publisher'] = f"{src_contact.get('name', '')}; {src_contact.get('address', '')}"
    ET.SubElement(contact, 'name').set('value', data.get('publisher',''))
    ET.SubElement(cs, 'description').set('value', data.get('description',''))
    ET.SubElement(cs, 'copyright').set('value', data.get('copyright',''))
    ET.SubElement(cs, 'caseSensitive').set('value', 'true')
    ET.SubElement(cs, 'content').set('value', 'not-present')

    tree = ET.ElementTree(cs)
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    error_count = qc_report(data)
    print(f"QC Reported {error_count} warnings/errors.")

def main():
    """
    Scrape the tables from a confluence page and write to a CodeSystem artefact
    """ 
    homedir=os.environ['HOME']
    parser = argparse.ArgumentParser()
    defaultpath=os.path.join(homedir,"data","hta")
    parser.add_argument("-r", "--csdir", help="cs data folder", default=defaultpath)
    parser.add_argument("-n", "--name", help="CodeSystem name", default='clinVarV')
    parser.add_argument("-p", "--page", help="page number", default='81028287')   
    args = parser.parse_args()
    ## Create the data path if it doesn't exist
    check_path(args.csdir)

    ## docs for confluence rest API https://docs.atlassian.com/ConfluenceServer/rest/7.19.2/
    ##  Example: url = f'https://confluence.hl7.org/rest/content/{args.page}'
    url = f'https://confluence.hl7.org/pages/viewpage.action?pageId={args.page}'
    # Get the access token that you set up to access Confluence using a script
    # Read the API token from the 'access.token' file
    # With thanks to Joshua Procious for the hint on how to get past the 403 Forbidden error
    with open('access.token', 'r') as file:
        api_token = file.read().strip()
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    } 
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    tables = soup.find_all('table')
    outdir = args.csdir
    for i, table in enumerate(tables):
        table_html = str(table)
        df = pd.read_html(StringIO(table_html))[0]        
        xml_fn = os.path.join(outdir, f"cs-{args.name}.xml")
        cs_df_to_xml(df, xml_fn)
        print(f'Transformed confluence page to {xml_fn}')



if __name__ == '__main__':
    main()
