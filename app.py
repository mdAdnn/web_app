import streamlit as st
import pandas as pd
import psycopg2

def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

def process_jsonb_columns(df):
    for col in df.columns:
        if isinstance(df[col][0], dict):
            df[col] = df[col].apply(lambda x: ', '.join([f"{k}: {v}" for k, v in x.items()]))
    return df

def main():
    try:
        conn = init_connection()
        cur = conn.cursor()

        # Query to get all unique gene symbols from cpic.gene_result table
        cur.execute("SELECT DISTINCT genesymbol FROM cpic.gene_result")
        gene_symbols = [row[0] for row in cur.fetchall()]

        # Create the first dropdown for gene symbols
        selected_gene_symbol = st.sidebar.selectbox("Select Gene Symbol", gene_symbols)

        # Query to get all unique diplotypes for the selected gene symbol from cpic.diplotype_phenotype table
        cur.execute(f"SELECT DISTINCT diplotype->>'{selected_gene_symbol}' AS simplified_diplotype FROM cpic.diplotype_phenotype WHERE jsonb_exists(diplotype, '{selected_gene_symbol}')")
        diplotypes = [row[0] for row in cur.fetchall()]

        # Create the second dropdown for simplified diplotypes related to the selected gene symbol
        selected_diplotypes = st.sidebar.selectbox("Select Diplotypes", diplotypes)

        # Add a submit button
        if st.sidebar.button("Submit"):
            # Construct and execute the query using selected values
            query = f"""
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
            # Execute the query and display the result
            cur.execute(query)
            result = cur.fetchall()

            # Get column names
            col_names = [desc[0] for desc in cur.description]

            # Create a DataFrame from the result
            df_result = pd.DataFrame(result, columns=col_names)

            # Process JSONB columns
            df_result = process_jsonb_columns(df_result)

            # Check if there are results to add to the HTML report
            if not df_result.empty:
                # Add the result DataFrame to the HTML report with styling to fit the page
                html_report = f"<a name='{selected_gene_symbol}_{selected_diplotypes}'></a>\n"
                html_report += f"<h3>Results for Genesymbol: {selected_gene_symbol}, Diplotype: {selected_diplotypes}</h3>\n"
                html_report += "<div style='overflow-x:auto;'>\n"
                html_report += df_result.to_html(index=False, escape=False, classes='report-table', table_id='report-table') + "\n"
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

if __name__ == '__main__':
    main()

