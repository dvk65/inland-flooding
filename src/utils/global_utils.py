"""
This script includes the functions used as a module in multiple scripts.  

This file can be imported as a module and includes the following functions:
    * print_func_header - print a summary of the running function;
"""

def print_func_header(var):
    print('-----------------------------------------------------------------------')
    print(f'{var}...\n')

def describe_df(df, var):
    print(f'\n{var} dataset overview:')
    df.info()
    print(df.head())

    attr_type_list = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, list)).any()]
    print('\nattributes (data type - list):\n', attr_type_list)

    num_unique = df[[col for col in df.columns if col not in attr_type_list]].nunique()
    print('\ncount of unique values in each attribute (non-list):\n', num_unique)