import streamlit as st
import pandas as pd
import psycopg2

def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

def main():
    try:
        conn = init_connection()
        cur = conn.cursor()

        # Query to get all unique gene symbols from cpic.gene_result table
        cur.execute("SELECT DISTINCT genesymbol FROM cpic.gene_result")
        gene_symbols = [row[0] for row in cur.fetchall()]

        # Create first dropdown for gene symbols
        selected_gene_symbol = st.sidebar.selectbox("Select Gene Symbol", gene_symbols)

        # Query to get all unique diplotypes for the selected gene symbol from cpic.diplotype_phenotype table
        cur.execute(f"SELECT DISTINCT diplotype FROM cpic.diplotype_phenotype WHERE jsonb_exists(diplotype, '{selected_gene_symbol}')")
        diplotypes = [row[0] for row in cur.fetchall()]

        # Create second dropdown for diplotypes related to the selected gene symbol
        selected_diplotypes = st.sidebar.selectbox("Select Diplotypes", diplotypes)

    except Exception as e:
        st.error(f"Error: {str(e)}")

    finally:
        # Close cursor and connection
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
