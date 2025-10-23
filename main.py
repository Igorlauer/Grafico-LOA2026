import pandas as pd
from dash import Dash, dcc, html, Input, Output, ctx
import plotly.express as px

# Dados
df = pd.read_excel('data/LOA 25 - 26 - GOIAS graifc.xlsx')
df['%4'] = df['%4'].astype(str).str.replace('%','').str.replace(',','.').astype(float)
df['%3'] = df['%3'].astype(str).str.replace('%','').str.replace(',','.').astype(float)
# Criação das novas colunas de percentual de investimento no orçamento do ano
df['% Investimento 2025'] = 100 * df['INVESTIMENTO 25'] / df['ORÇAMENTO 25']
df['% Investimento 2026'] = 100 * df['INVESTIMENTO 26'] / df['ORÇAMENTO 26']

colunas_grafico = {
    'Orçamento 2025': 'ORÇAMENTO 25',
    'Investimento 2025': 'INVESTIMENTO 25',
    '% Investimento 2025': '% Investimento 2025',
    'Orçamento 2026': 'ORÇAMENTO 26',
    'Investimento 2026': 'INVESTIMENTO 26',
    '% Investimento 2026': '% Investimento 2026',
    'Δ Orçamento (absoluto)': 'ORÇAMENTO',
    'Δ Investimento (absoluto)': 'INVESTIMENTO',
    'Δ Orçamento (%)': '%4',
    'Δ Investimento (%)': '%3'
    
   
}
invcol = {v: k for k, v in colunas_grafico.items()}

app = Dash(__name__)

app.layout = html.Div([
    # Header com logo e título
    html.Div([
        html.H2("Comparativo de Orçamento & Investimento — LOA 2025 x 2026", style={'marginBottom': 0}),
        html.Img(
            src='https://storage.jamilcalife.com.br/uploads/arquivo-1761254396730-629944080.png',
            style={'height':'60px', 'marginLeft': 'auto'}
        )
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'justifyContent': 'space-between',
        'alignItems': 'center',
        'marginBottom': '20px'
    }),
    
    html.Label("Macro grupo"),
    dcc.Dropdown(
        id='macro-dropdown',
        options=[{'label': 'Todos', 'value': '__todos__'}] + [{'label': i, 'value': i} for i in df['Macro grupo'].dropna().unique()],
        value='__todos__'
    ),

    html.Label("SubGrupo"),
    dcc.Dropdown(id='subgrupo-dropdown', value='__todos__'),

    html.Label("Órgão"),
    dcc.Dropdown(id='orgao-dropdown', multi=True, value=['__todos__']),

    html.Br(),
    html.Label("Selecione as colunas para gráfico (pode multi-selecionar)"),
    dcc.Dropdown(
        id='colunas-grafico-dropdown',
        options=[{'label': k, 'value': v} for k, v in colunas_grafico.items()],
        value=['ORÇAMENTO 25', 'ORÇAMENTO 26'],  # default 2 barras
        multi=True,
        maxHeight=200
    ),

    # O gráfico: só uma vez!
    dcc.Graph(id='grafico'),

    # Rodapé/legenda
    html.Div(
        "As porcentagens representam a relação entre investimento e orçamento de cada órgão, por ano. "
        "Documentos fonte: LOA 2025 e LOA 2026. - Produzido por: Igor Lauer - Assessor Parlamentar",
        style={
            'fontSize': '13px',
            'marginTop': '10px',
            'fontStyle': 'italic',
            'color': '#666',
            'textAlign': 'center'
        }
    )
])

# Atualiza SubGrupo: depende só de Macro
@app.callback(
    Output('subgrupo-dropdown', 'options'),
    Output('subgrupo-dropdown', 'value'),
    Input('macro-dropdown', 'value')
)
def atualiza_subgrupos(macro):
    if macro == '__todos__' or macro is None:
        subgrupos = df['SubGrupo'].dropna().unique()
    else:
        subgrupos = df[df['Macro grupo'] == macro]['SubGrupo'].dropna().unique()
    options = [{'label': 'Todos', 'value': '__todos__'}] + [{'label': i, 'value': i} for i in subgrupos]
    return options, '__todos__'

# Atualiza Órgãos: depende de Macro e SubGrupo
@app.callback(
    Output('orgao-dropdown', 'options'),
    Output('orgao-dropdown', 'value'),
    Input('macro-dropdown', 'value'),
    Input('subgrupo-dropdown', 'value')
)
def atualiza_orgaos(macro, subgrupo):
    dff = df.copy()
    if macro != '__todos__' and macro is not None:
        dff = dff[dff['Macro grupo'] == macro]
    if subgrupo != '__todos__' and subgrupo is not None:
        dff = dff[dff['SubGrupo'] == subgrupo]
    orgaos = dff['ORGÃO'].dropna().unique()
    options = [{'label': 'Todos', 'value': '__todos__'}] + [{'label': i, 'value': i} for i in orgaos]
    return options, ['__todos__']

# Gera gráfico: aceita 1, 2... N barras
@app.callback(
    Output('grafico', 'figure'),
    Input('macro-dropdown', 'value'),
    Input('subgrupo-dropdown', 'value'),
    Input('orgao-dropdown', 'value'),
    Input('colunas-grafico-dropdown', 'value')
)
def atualiza_grafico(macro, subgrupo, orgaos, colunas_selecionadas):
    dff = df.copy()
    # Filtro macro
    if macro != '__todos__' and macro is not None:
        dff = dff[dff['Macro grupo'] == macro]
    # Filtro subgrupo
    if subgrupo != '__todos__' and subgrupo is not None:
        dff = dff[dff['SubGrupo'] == subgrupo]
    # Filtro órgão
    if orgaos and '__todos__' not in orgaos:
        dff = dff[dff['ORGÃO'].isin(orgaos)]
    # Não há selecionados válidos
    if dff.empty or not colunas_selecionadas:
        return px.bar(title="Sem dados para esse filtro")
    # Garante lista
    if isinstance(colunas_selecionadas, str):
        colunas_selecionadas = [colunas_selecionadas]
    fig = px.bar(
        dff,
        y="ORGÃO",
        x=colunas_selecionadas,
        orientation='h',
        barmode='group',
        labels={'value': 'Valor / Variação', 'ORGÃO': 'Órgão', 'variable': 'Indicador'},
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.for_each_trace(lambda t: t.update(name=invcol.get(t.name, t.name)))
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig

if __name__ == '__main__':
    app.run(debug=True)