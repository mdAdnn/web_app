import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

def process_jsonb_columns(df):
    for col in df.columns:
        if isinstance(df[col][0], dict):
            df[col] = df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))
    return df

def execute_custom_query(selected_gene_symbol, selected_diplotypes, selected_drug):
    print(f"Selected Gene Symbol: {selected_gene_symbol}")
    print(f"Selected Diplotypes: {selected_diplotypes}")
    print(f"Selected Drug: {selected_drug}")
    
    if selected_gene_symbol == "None" and selected_diplotypes == "None" and selected_drug == "None":
        # Return all data if "None" is selected in all dropdowns
        print("No input selected")
    elif selected_gene_symbol and selected_diplotypes and selected_drug and selected_drug != "None":
        # Construct the SQL query for gene symbol, diplotypes, and drug
        sql_query = f"""
            SELECT DISTINCT ON (p.drugid)
                dp.*,
                p.drugid,
                dr.name,
                r.drugrecommendation,
                r.classification
            FROM cpic.gene_result_diplotype d
            JOIN cpic.gene_result_lookup l ON d.functionphenotypeid = l.id
            JOIN cpic.gene_result gr ON l.phenotypeid = gr.id
            JOIN cpic.pair p ON gr.genesymbol = p.genesymbol
            JOIN cpic.drug dr ON p.drugid = dr.drugid
            JOIN cpic.recommendation r ON dr.drugid = r.drugid
            JOIN cpic.diplotype_phenotype dp ON r.phenotypes = dp.phenotype
            WHERE dp.diplotype ->> '{selected_gene_symbol}' = '{selected_diplotypes}'
                AND dr.name = '{selected_drug}'
                AND r.classification <> 'No Recommendation'
                AND r.drugrecommendation <> 'No recommendation'
            ORDER BY p.drugid, r.classification;
        """
    elif selected_gene_symbol and selected_diplotypes:
        # Construct the SQL query for gene symbol and diplotypes without filtering by drug name
        sql_query = f"""
            SELECT DISTINCT ON (p.drugid)
                dp.*,
                p.drugid,
                dr.name,
                r.drugrecommendation,
                r.classification
            FROM cpic.gene_result_diplotype d
            JOIN cpic.gene_result_lookup l ON d.functionphenotypeid = l.id
            JOIN cpic.gene_result gr ON l.phenotypeid = gr.id
            JOIN cpic.pair p ON gr.genesymbol = p.genesymbol
            JOIN cpic.drug dr ON p.drugid = dr.drugid
            JOIN cpic.recommendation r ON dr.drugid = r.drugid
            JOIN cpic.diplotype_phenotype dp ON r.phenotypes = dp.phenotype
            WHERE dp.diplotype ->> '{selected_gene_symbol}' = '{selected_diplotypes}'
                AND r.classification <> 'No Recommendation'
                AND r.drugrecommendation <> 'No recommendation'
            ORDER BY p.drugid, r.classification;
        """
    elif selected_drug:
        sql_query = f"""
            select distinct d.name,
	            d.drugid,
	            r.drugrecommendation,
	            r.classification,
	            r.phenotypes
            from cpic.drug d
            join cpic.recommendation r on d.drugid = r.drugid
            where name = '{selected_drug}'
            AND r.classification <> 'No Recommendation'
            AND r.drugrecommendation <> 'No recommendation'
            ORDER BY d.drugid, r.classification;
        """
    else:
        # Handle other cases or provide a default query
        sql_query = ""

    # Execute the SQL query
    if sql_query:
        conn = init_connection()
        cur = conn.cursor()
        cur.execute(sql_query)

        # Fetch the results
        result = cur.fetchall()

        # Convert the results to a Pandas DataFrame
        df = pd.DataFrame(result, columns=[desc[0] for desc in cur.description])

        return df
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no query is selected

def main():
    try:
        conn = init_connection()
        cur = conn.cursor()
        
        # Query to get all unique gene symbols from cpic.gene_result table
        cur.execute("SELECT DISTINCT genesymbol FROM cpic.gene_result")
        gene_symbols = ["None"] + [row[0] for row in cur.fetchall()]

        # Create the first dropdown for gene symbols
        selected_gene_symbol = st.sidebar.selectbox("Select Gene Symbol", gene_symbols)

        # Query to get all unique diplotypes for the selected gene symbol from cpic.diplotype_phenotype table
        cur.execute(f"SELECT DISTINCT diplotype->>'{selected_gene_symbol}' AS simplified_diplotype FROM cpic.diplotype_phenotype WHERE jsonb_exists(diplotype, '{selected_gene_symbol}')")
        diplotypes = [row[0] for row in cur.fetchall()]

        # Create the second dropdown for simplified diplotypes related to the selected gene symbol
        selected_diplotypes = st.sidebar.selectbox("Select Diplotypes", diplotypes)

        # Create third dropdown for drugs
        cur.execute("SELECT DISTINCT name FROM cpic.drug")
        drugs = ["None"] + [row[0] for row in cur.fetchall()]
        selected_drug = st.sidebar.selectbox("Select Drug", drugs)
        
        # Add a submit button
        if st.sidebar.button("Submit"):
            # Execute the custom query with the selected drug name
            result_df = execute_custom_query(selected_gene_symbol, selected_diplotypes, selected_drug)

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
                # Process JSONB columns
                result_df = process_jsonb_columns(result_df)

            # Check if there are results to add to the HTML report
            if not result_df.empty:
                # Add the result DataFrame to the HTML report with styling to fit the page
                html_report = f"<a name='{selected_gene_symbol}_{selected_diplotypes}'></a>\n"
                html_report += f"<h3>Results for  {selected_gene_symbol}, {selected_diplotypes}</h3>\n"
                html_report += "<div style='overflow-x:auto;'>\n"
                html_report += result_df.to_html(index=False, escape=False, classes='report-table', table_id='report-table', justify='center') + "\n"
                html_report += "</div>\n"

                # Display the HTML report
                st.markdown(html_report, unsafe_allow_html=True)

            else:
                st.warning(f"No results found for Genesymbol: {selected_gene_symbol}, Diplotype: {selected_diplotypes}")


    except Exception as e:
        st.error(f"Error: {str(e)}")

    finally:
        # Close cursor and connection
        cur.close()
        conn.close()

# Custom Streamlit app header
st.markdown(
    """
    <div style='display: flex; background-color: #ADD8E6; padding: 10px; border-radius: 10px;'>
        <h1 style='margin-right: 20px; color: purple;'>Pharmacogenomic Analysis</h1>
        <img src='https://www.hbku.edu.qa/sites/default/files/media/images/hbku_2021.svg' style='align-self: flex-end; width: 200px; margin-left: auto;'>
    </div>
    """,
    unsafe_allow_html=True
)

# File upload
uploaded_file = st.file_uploader("Choose a .txt file", type="txt")

if uploaded_file is not None:
    # Read the content of the file and decode bytes to string
    file_contents = uploaded_file.read().decode('utf-8')

    # Extract name, id, and timestamp
    lines = file_contents.split('\n')
    name = lines[0].split(':')[-1].strip()
    user_id = lines[1].split(':')[-1].strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Display name, id, and timestamp at the top
    st.write(f"Name: {name}")
    st.write(f"ID: {user_id}")
    st.write(f"Timestamp: {timestamp}")

    # Assume the file content contains genesymbol and diplotype separated by a comma
    pairs = [line.split(',') for line in lines[3:]]

    # Initialize the HTML string
    html_report = ""

    for idx, pair in enumerate(pairs, start=1):
        # Check if the pair contains both genesymbol and diplotype
        if len(pair) == 2:
            genesymbol, diplotype = pair          

            # Execute the SQL query with the provided genesymbol and diplotype
            result_df = execute_custom_query(genesymbol.strip(), diplotype.strip(), selected_drug="None")

            # Check if the DataFrame is not empty before processing
            if not result_df.empty:
                # Process columns with JSONB format to remove {}
                for col in result_df.columns:
                    if isinstance(result_df[col][0], dict):
                        result_df[col] = result_df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))

                result_df.index += 1
                
                # Add the result DataFrame to the HTML report
                html_report += f"<a name='{genesymbol}_{diplotype}'></a>\n"
                html_report += f"<h3>Results for {genesymbol}, {diplotype}</h3>\n"
                html_report += result_df.to_html(index=False, escape=False, classes='report-table', table_id='report-table', justify='center') + "\n"

                
            else:
                st.warning(f"No results found for Genesymbol: {genesymbol}, Diplotype: {diplotype}")

    # Display the entire HTML report
    st.markdown(html_report, unsafe_allow_html=True)
    st.write("#")
    # End the report with reduced font size
    st.write("###### End of Report")
    label = r'''
    $\text {
        \scriptsize Genotypes were called using Aldy, Actionable drug interactions were collected from CPIC database.
    }$ 
    '''
    st.write(label)

if __name__ == '__main__':
    main()
