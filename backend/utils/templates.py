main_template = """
Input Table Columns MetaData with Sample values:
{info_input}

Output Table Columns MetaData with Sample values:
{info_template}

Objective: Map the columns of the input table to the output table, considering the logical,
linguistic, and contextual relationship between column names, format of values and sample
values in both tables.

Guidelines:
1. For each column in the output table, suggest mapped column(s) from the input table having
   similar values with output table.
2. Provide a brief rationale (up to 4 words) for each mapping suggestion.
3. Point out any changes or transformations required in the input table data to conform to the
   output table format.
Finally share the working Python script that has a method named map_columns which can perform
the suggested mappings and data transformations by extracting data from the input dataframe
`input_df` and return a pandas dataframe. Also provide the invoke statement of the method and
store the result in a variable named mapped_df. Use only pandas (pd), numpy (np) and datetime,
and do not read or write files.

Give me the response in the format below:
Suggestions:
Rationale:
Code:
"""

revision_template = """
Input Table Columns MetaData with Sample values:
{info_input}

Output Table Columns MetaData with Sample values:
{info_template}

Objectives:
For each column in the output table, suggest mapped column(s) from the input table having
similar values and format of values with output table.
Provide a brief rationale (up to 4 words) for each mapping suggestion.
Also, your goal is to use the column names written under Mapped Columns {suggestion} for
generating the python script.
Your Goal: Finally share the working Python script that has a method named map_columns which
can perform the mappings of Mapped Columns and data transformations by taking the input
dataframe `input_df` and returning a pandas dataframe. Ensure to provide the invoke statement
to call the method and store the result in a variable named mapped_df. Use only pandas (pd),
numpy (np) and datetime, and do not read or write files.

Response Format:
Mapped Columns: (Columns Mapping)
Rationale:
Code:
"""
