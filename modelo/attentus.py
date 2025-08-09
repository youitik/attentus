import pulp as plp
from itertools import product
from utilidades.utils import retorna_lista

def attentus(df_nan, df_nad, minutos_dividir):
    regimes = \
        df_nad["regime"].to_dict()
    inicios = \
        df_nan["hora_inicio"].to_dict()
    
    lista_variaveis = list(product(regimes, inicios))

    prob = plp.LpProblem(
        name="Attentus", sense=plp.LpMinimize
    )
    
    pulp_variaveis = plp.LpVariable.dicts(
        "A", lista_variaveis, lowBound=0, cat=plp.LpInteger
    )

    coeficientes = []
    for indice_regime, indice_periodo in lista_variaveis:
        encargo = df_nad.loc[indice_regime, "enc"]
        coeficientes.append(encargo)

    fo = plp.lpSum(
        [coef * pulp_variaveis[var] 
        for coef, var in zip(coeficientes, lista_variaveis)]
    )
    prob += fo, "custo"

    for j, linha in df_nan.iterrows():
        nan = linha["nan"]
        linha_restricao = []
        for indice_regime, regime in regimes.items():
            tamanho = int(regime * 60 / minutos_dividir)
            lista = retorna_lista(j=j, tamanho=tamanho,
                                lista_momentos=list(inicios))
            
            lista_combinada = [(indice_regime, i) for i in lista]
            lista_traduzida = [pulp_variaveis[tupla] 
                            for tupla in lista_combinada]
            
            linha_restricao += lista_traduzida
        prob += plp.lpSum(linha_restricao) >= nan
    
    solver = plp.getSolver('PULP_CBC_CMD')
    prob.solve(solver)
    return prob