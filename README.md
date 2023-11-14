# web_app
<p>create a secrets.toml file and save the postgresql credentials</p><br>

# Dependencies
<li>streamlit</li>
<li>psycopg2</li>
<li>wkhtmltopdf</li>
<p>Download the wkhtmltopdf from the website. Run it on your system.</p>
<p>After installing wkhtmltopdf, make sure it's in your system's PATH.</p><br>

'''
pdfkit.from_string(html_report, pdf_report, options={'quiet': '', 'path': '/path/to/wkhtmltopdf'});
'''

Replace '/path/to/wkhtmltopdf' with the actual path where wkhtmltopdf is installed on your system.

Make sure to restart your Streamlit app after installing wkhtmltopdf and making any changes to your code.
