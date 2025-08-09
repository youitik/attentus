import streamlit as st
import pandas as pd
from pulp import LpStatus
from utilidades.utils import (gerar_tabela_nan,
                              ajusta_polinomio,
                              encontra_divisores,
                              lista_turnos_possiveis,
                              gera_tabelas,
                              gera_resultados)

from modelo.attentus import attentus

def main():
    st.title("Attentus")
    st.sidebar.title("Configs")

    qtd_horas_total = st.sidebar.number_input(
        "Qtd. de horas total do dia para trabalhar",
        min_value=5,
        max_value=48,
        value=24,
        step=1
    )

    st.sidebar.divider()

    colunas = st.sidebar.columns(2)
    hora_inicial = colunas[0].number_input(
        "Hora inicial do dia (0-23)",
        min_value=0, max_value=23, value=0, step=1
    )

    minuto_inicial = colunas[1].number_input(
        "Minuto final do dia (0-59)",
        min_value=0, max_value=59, value=0, step=1
    )

    st.sidebar.divider()

    qtd_dias_total = qtd_horas_total / 24
    qtd_minutos_total = qtd_horas_total * 60

    divisores = encontra_divisores(qtd_minutos_total)
    minutos_dividir = st.sidebar.selectbox(
        "Dividir o dia em quantos minutos",
        options=divisores,
        index=divisores.index(15)
    )

    st.sidebar.divider()

    turnos_possiveis = lista_turnos_possiveis(1, 
                                              qtd_horas_total,
                                              minutos_dividir)
    
    dict_turnos_possiveis = {}
    for turno in turnos_possiveis:
        horas = int(turno)
        minutos = int((turno - horas) * 60)
        dict_turnos_possiveis[f"{horas:02}h{minutos:02}"] = turno

    qtd_turnos = st.sidebar.number_input(
        "Quantidade de turnos possíveis",
        min_value = 1,
        max_value = 5,
        value = 3,
        step = 1
    )

    turnos = []
    encargos = []

    for i in range (qtd_turnos):
        col1, col2 = st.sidebar.columns(2)

        turno = col1.selectbox(
            f"Turno {i + 1}",
            options=list(dict_turnos_possiveis),
            index=i
        )

        encargo = col2.number_input(
            f"Encargo do turno {i + 1}",
            min_value=100,
            max_value=5000,
            value=540
        )

        turnos.append(dict_turnos_possiveis[turno])
        encargos.append(encargo)

    st.sidebar.divider()

    tempo_descanso = st.sidebar.number_input(
        "Tempo de descanso entre atendimentos (segundos)",
        min_value=0,
        max_value=1000, 
        value=0,
        step=1
    )

    tempo_maximo_espera = st.sidebar.number_input(
        "Tempo maximo de espera para atendimento (segundos)",
        min_value=0,
        max_value=1000, 
        value=10,
        step=1
    )

    grau_polinomio = st.sidebar.number_input(
        "Grau do polinomio para modelo de previsao",
        min_value=0,
        max_value=10, 
        value=2,
        step=1
    )


    st.sidebar.divider()

    df_nad, df_tabela_ligantes = gera_tabelas(
        qtd_horas_total,
        minutos_dividir,
        hora_inicial,
        minuto_inicial,
        turnos,
        encargos
    )

    #df_tabela_ligantes

    st.sidebar.download_button(
        "Download do template df_tabela_ligantes",
        data=df_tabela_ligantes.to_csv(index=False).encode("utf-8"),
        file_name="df_tabela_ligantes.csv",
        mime="text/csv"
    )

    arquivo_duracoes = st.sidebar.file_uploader(
        "Carregar arquivo de durações preenchidas",
        type=["csv", "xlsx"]
    )

    if arquivo_duracoes is not None:
        df_duracoes = pd.read_excel(arquivo_duracoes)

    arquivo_ligantes = st.sidebar.file_uploader(
        "Carregar arquivo de ligantes por períodos preenchidos",
        type=["xlsx"]
    )

    if arquivo_ligantes is not None:
        df_tabela_ligantes = pd.read_excel(arquivo_ligantes)
    
    st.sidebar.divider()

    opcao = st.sidebar.segmented_control(
        options = ["Ajustar Polinomio",
                   "Rodar Attentus"],
        label = "Escolha a opção",
        default = "Rodar Attentus",
        selection_mode="single"
    )

    botao = st.sidebar.button("Avançar")

    if (opcao == "Ajustar Polinomio" 
        and botao 
        and arquivo_duracoes):
        fig = ajusta_polinomio(df_duracoes, grau_polinomio)
        st.pyplot(fig)
    elif (opcao == "Rodar Attentus"
          and botao
          and arquivo_ligantes
          and arquivo_duracoes
          ):
        
        #print("RODAR MODELO !!!!!!")
        coluna_nan = gerar_tabela_nan(df_tabela_ligantes,
                                      df_duracoes,
                                      tempo_maximo_espera,
                                      tempo_descanso,
                                      grau_polinomio
                                      )

        df_tabela_ligantes["nan"] = coluna_nan

        prob = attentus(df_nan = df_tabela_ligantes,
                        df_nad = df_nad,
                        minutos_dividir=minutos_dividir)
        
        status = LpStatus[prob.status]
        print(status)

        if status != "Optimal":
            st.error(f"Erro ao resolver o modelo {status}")
            return
        
        regimes = df_nad["regime"].to_dict()
        inicios = df_tabela_ligantes["hora_inicio"].to_dict()
        df_resultados = gera_resultados(prob, regimes, inicios)
        df_totais = df_resultados.sum()

        st.dataframe(df_resultados)
        st.dataframe(df_totais.reset_index(name="total atendentes"),
                     hide_index=True
                     )
        st.success(f"Custo Total: R$ {prob.objective.value():,.2f}")



if __name__ == "__main__":
    main()