import numpy as np
import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

def change_date(df):
    df.columns = [pd.to_datetime(col, errors='ignore').strftime('%d-%m-%Y') for col in df.columns]
    return df


def substraction_of_metrics(df, first_summand, second_summand, name_of_new_metric):
    assets = df.loc[df['Financial Indicators'] == first_summand].iloc[0]
    debt = df.loc[df['Financial Indicators'] == second_summand].iloc[0]
    na = assets.iloc[2:] - debt.iloc[2:]
    new_row = pd.DataFrame([[name_of_new_metric, 'bs' ] + list(na)], columns=df.columns)
    df = pd.concat([df, new_row], ignore_index=False)

    return df


def year_averages(df, financial_indicator):
    # get the data of the indicator so to calc average
    indicator_data = df.loc[df['Financial Indicators'] == financial_indicator, df.columns[2:]]

    # calculate moving average
    avg_balances = [
        np.nanmean(indicator_data.iloc[:, col -2:col].values)
        for col in range(2, len(df.columns)) 
        ]
    # create new row
    new_row_data = pd.DataFrame([[financial_indicator + ' MA', 'bs'] + avg_balances], columns=df.columns)
 
    # insert the new rows into the original df
    df = pd.concat([df, pd.DataFrame(new_row_data, columns=df.columns)], ignore_index=True)

    return df


def get_data(ticker):
    # call data
    company = yf.Ticker(ticker=ticker)
    bs, income, cf = company.balance_sheet, company.income_stmt, company.cash_flow
    
    # adjust datetype for columns
    bs = change_date(bs)
    income = change_date(income)
    cf = change_date(cf)

    #add data source
    bs.insert(0, 'Data Source', 'bs')
    income.insert(0, 'Data Source', 'is')
    cf.insert(0, 'Data Source', 'cf')

    # produce final table
    fin_table = pd.concat([bs, income, cf])
    fin_table = fin_table.reset_index().rename(columns={'index': 'Financial Indicators'})
    
    # add net assets
    fin_table = substraction_of_metrics(fin_table, 'Total Assets', 'Total Debt', 'Net Assets')

    # add year averages for 
    fin_table = year_averages(fin_table, 'Total Assets')
    fin_table = year_averages(fin_table, 'Accounts Receivable')
    fin_table = year_averages(fin_table, 'Inventory')
    
    return fin_table


def get_rate(df, nom, denom, nom_source, denom_source ,year = False):

    nom_data = df[(df['Financial Indicators'] == nom) & (df['Data Source'] == nom_source)]
    denom_data = df[(df['Financial Indicators'] == denom) & (df['Data Source'] == denom_source)]
    
    nom_values=nom_data.iloc[:,2:].values
    denom_values=denom_data.iloc[:,2:].values
    
    rate=nom_values/denom_values
    if year:
        rate = rate * 365
   
    calc = pd.DataFrame(rate, columns=df.columns[2:])
    
    return calc



def plot_ccc_trend(chart_data, year):
    chart_data['ccc'] = chart_data['dso'] + chart_data['ito'] - chart_data['dpo']
    data = chart_data.loc[year]
    # Define measures for waterfall chart
    measures = ['relative', 'relative', 'relative', 'total']
    # Create a Waterfall chart
    fig = go.Figure(go.Waterfall(
        name="Cash Conversion Cycle",
        orientation="v",
        measure=measures,
        x=['DSO', 'ITO', '-DPO', 'CCC'],
        textposition="outside",
        y=[data['dso'], data['ito'], -data['dpo'], data['ccc']],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    fig.update_layout(
        title=f"Cash Conversion Cycle (CCC) in {year}",
        showlegend=True
    )
    return fig


st.set_page_config(layout="wide")
#------ INIALISAION OF APP
# create session state -> will st.session_state can store data inside of it
def initialise_session_state():
    if 'submissions' not in st.session_state:
        st.session_state['submissions'] = []
    if 'compare_mode' not in st.session_state:
        st.session_state['compare_mode'] = False


# Handle submission -> after the button is clicked, retrived data is stored
# TODO check if it makes sence to save computed metrics in cache as well

def handle_submission():
    result_df = get_data(user_input)

    # compute key metrics of a company
    net_income = get_rate(result_df,'Net Income', 'Total Revenue', 'is', 'is')
    gross_margin_rate = get_rate(result_df,'Gross Profit', 'Total Revenue', 'is', 'is')
    fcf_to_revenue = get_rate(result_df, 'Free Cash Flow', 'Total Revenue', 'cf', 'is')
    cash_conversion_rate = get_rate(result_df, 'Operating Cash Flow', 'Net Income', 'cf', 'is')
    dso = get_rate(result_df, 'Accounts Receivable MA', 'Total Revenue', 'bs', 'is', year=True)
    ito = get_rate(result_df, "Inventory MA","Cost Of Revenue","bs","is", year=True)
    dpo = get_rate(result_df, "Accounts Payable","Cost Of Revenue","bs","is", year=True)
    assert_Turnover_Rate = get_rate(result_df, "Total Revenue", "Total Assets MA", "is", "bs")
    Current_Ratio =  get_rate(result_df, "Current Assets", "Current Liabilities", "bs", "bs")
    Solvency = get_rate(result_df, "EBIT","Interest Expense","is","is")
    
    Total_Revenue = result_df[(result_df['Financial Indicators']=='Total Revenue')].iloc[:,2:]
    Cost_of_Revenue = result_df[(result_df['Financial Indicators']=='Cost Of Revenue')].iloc[:,2:]
    Gross_Profit = result_df[(result_df['Financial Indicators']=='Gross Profit')].iloc[:,2:]
    Selling = result_df[(result_df['Financial Indicators']=='Selling General And Administration')].iloc[:,2:]
    ebit = result_df[(result_df['Financial Indicators']=='EBIT')].iloc[:,2:]
    Interest_Expense = result_df[(result_df['Financial Indicators']=='Interest Expense')].iloc[:,2:]
    Net_Income = result_df[(result_df['Financial Indicators']=='Net Income')].iloc[:,2:]
    Net_Income_Operations= result_df[(result_df['Financial Indicators']=='Net Income From Continuing Operations')].iloc[:,2:]
    Cash_Flow_Financing = result_df[(result_df['Financial Indicators']=='Cash Flow From Continuing Financing Activities')].iloc[:,2:]
    Cash_Flow_Investing = result_df[(result_df['Financial Indicators']=='Cash Flow From Continuing Investing Activities')].iloc[:,2:]
    Cash_Flow_Operating = result_df[(result_df['Financial Indicators']=='Cash Flow From Continuing Operating Activities')].iloc[:,2:]
    Changes_In_Cash = result_df[(result_df['Financial Indicators']=='Changes In Cash')].iloc[:,2:]
    # Append the DataFrame and input to the session state
    
    st.session_state['submissions'].append({
        'input': user_input, 
        'result': result_df,
        'net_income': net_income ,
        'Gross Margin Rate':gross_margin_rate,
        'Free Cash Flow to Revenue': fcf_to_revenue,
        'Cash Conversion Rate': cash_conversion_rate,
        'dso':dso,
        'ito':ito,
        'dpo':dpo,
        'Asset Turnover Rate':assert_Turnover_Rate,
        'Current Ratio':Current_Ratio,
        'Solvency':Solvency,
        'Total_Revenue':Total_Revenue,
        'Cost_of_Revenue':Cost_of_Revenue,
        'Gross_Profit':Gross_Profit,
        'Selling':Selling,
        'ebit':ebit,
        'Interest_Expense':Interest_Expense,
        'Net_Income':Net_Income,
        'Net_Income_Operations':Net_Income_Operations,
        'Cash_Flow_Financing':Cash_Flow_Financing,
        'Cash_Flow_Investing':Cash_Flow_Investing,
        'Cash_Flow_Operating':Cash_Flow_Operating,
        'Changes_In_Cash':Changes_In_Cash
    })
    st.session_state['compare_mode'] = False

initialise_session_state()
# App main interface
# header
st.title('Financial Analysis Engine Dashboard')
# Sidebar for input and submission
user_input = st.sidebar.text_input("Enter ticker of a company", "")
submit_button = st.sidebar.button('Submit', on_click=handle_submission)

submission1 = submission2 = selected_view = selected_submission= None # initialise empty vars for the comparisson mode

# # Dropdown for selecting a company to view
if st.session_state.get('submissions'):
    view_options = [submission['input'] for submission in st.session_state['submissions']]
    selected_view = st.sidebar.selectbox('Select a company to view', view_options, key='selected_view')
    selected_submission = next((sub for sub in st.session_state['submissions'] if sub['input'] == selected_view), None)

    # Reset comparison mode when a new company is selected to view
    if selected_view and st.session_state.get('compare_mode') and st.session_state.get('last_view') != selected_view:
        st.session_state['compare_mode'] = False
    st.session_state['last_view'] = selected_view

# Dropdowns and button for comparison mode -> comparisson mode will appear when more than one company will be submitted
if st.session_state.get('submissions') and len(st.session_state['submissions']) > 1:
    st.sidebar.write("----")
    st.sidebar.write("Comparison Mode")
    company1 = st.sidebar.selectbox('Select the first company', view_options, key='company1')
    company2 = st.sidebar.selectbox('Select the second company', view_options, key='company2')
    compare_button = st.sidebar.button('Compare')

    # if you click on the button, it will check whether two companies are not equal and then
    if compare_button and company1 != company2:
        st.session_state['compare_mode'] = True
        submission1 = next((sub for sub in st.session_state['submissions'] if sub['input'] == company1), None)
        submission2 = next((sub for sub in st.session_state['submissions'] if sub['input'] == company2), None)

# Sidebar for selecting a company to view and comparison mode

#-------------------------------------DISPLAY LOGIC--------------------------#
# check if compare mode activated
# if yes -> it will display side by side comparisson #TODO -> replace it with overlapping graphs
# if not -> it will display one selected company 

if st.session_state.get('compare_mode') and submission1 and submission2:
    compare_list = ['Gross Margin Rate', 'Free Cash Flow to Revenue', 'Cash Conversion Rate', 'Asset Turnover Rate', "Current Ratio", 'Solvency']

    for i, ratio in enumerate(compare_list):
        if i % 3 == 0:
            cols = st.columns(3)

        with cols[i % 3]:
            st.header(ratio)

            # Preparing data for line chart
            sub1_data = submission1[f'{ratio}'].rename(columns={0: company1})
            sub2_data = submission2[f'{ratio}'].rename(columns={0: company2})
            sub1_data.columns = [col.split('-')[2] if '-' in col else col for col in sub1_data.columns]
            sub2_data.columns = [col.split('-')[2] if '-' in col else col for col in sub2_data.columns]
            
            # Combining data for chart
            chart_data = sub1_data.T
            chart_data.insert(1, company2, sub2_data.T) 
            chart_data = chart_data.rename(columns={0: company1})

            st.line_chart(chart_data)
    
else:
    # Show the selected submission if not in comparison mode
        if selected_submission:
            st.write(f"Ticker: {selected_submission['input']}")
            st.write('## Waterfall chart')
            time = st.selectbox('Selcet the period',(list(selected_submission['Gross_Profit'].columns)))
            waterfall = go.Figure(go.Waterfall(
                name = "", orientation = "v",
                measure = ["relative", "relative", "total", 
                            "relative", "relative", "total",
                            "relative", "relative", "total"],
                x = ["Total Revenue", "Cost of Revenue", "Gross Profit",
                        "Selling", "Others", "EBIT",
                        "Interest_Expense","Tax","Net Income"],
                textposition = "outside",
                y = [int(selected_submission['Total_Revenue'][time]), -int(selected_submission['Cost_of_Revenue'][time]), 0,
                     -int(selected_submission['Selling'][time]), 
                     -int(selected_submission['Gross_Profit'][time])+int(selected_submission['ebit'][time])+int(selected_submission['Selling'][time]), 0,
                     -int(selected_submission['Interest_Expense'][time]),
                     -int(selected_submission['ebit'][time])+int(selected_submission['Interest_Expense'][time])+int(selected_submission['Net_Income'][time]),0],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            waterfall.update_layout(
                    title = "Profit and loss statement "+time,
                    showlegend = True
            )
            
        
            waterfall1 = go.Figure(go.Waterfall(
                name = "", orientation = "v",
                measure = ["relative", "relative", "relative", "relative", "total"],
                x = ['Net Income Operations','Cash Flow From Continuing Financing Activities',
                     'Cash Flow From Continuing Investing Activities','Cash Flow From Continuing Operating Activities','Changes In Cash'],
                textposition = "outside",
                y = [int(selected_submission['Net_Income_Operations'][time]), 
                     int(selected_submission['Cash_Flow_Financing'][time]),
                     int(selected_submission['Cash_Flow_Investing'][time]), 
                     int(selected_submission['Cash_Flow_Operating'][time]),
                     0],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            waterfall1.update_layout(
                    title = "Cash flow in "+time,
                    showlegend = True
            )
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(waterfall, theme="streamlit",use_container_width=True) 
            with col2:
                st.plotly_chart(waterfall1, theme="streamlit",use_container_width=True) 
            
            ### second row of metrics
            chart_data = selected_submission['dso'].T
            chart_data.rename(columns={0: 'dso'}, inplace=True)
            chart_data.insert(1,'dpo',selected_submission['dpo'].T)
            chart_data.insert(1,'ito',selected_submission['ito'].T)
            st.header("DPO ITO and DSO")
            
            fig = plot_ccc_trend(chart_data, time)
            
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                st.plotly_chart(fig, use_container_width=True) 
            with col2:
                st.header("Gross Profit:")
                st.header("EBIT:")
                st.header("Net Income:")
                
            with col3:
                st.header('$ '+str(int(+selected_submission['Gross_Profit'][time])/1000000)+'M')
                st.header('$ '+str(int(+selected_submission['ebit'][time])/1000000)+'M')
                st.header('$ '+str(int(+selected_submission['Net_Income'][time])/1000000)+'M')
                
                

