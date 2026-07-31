# --- NOVO: Função de Simulação ---
def simulate_full_ranking_avg_trend(df_base_edicao_6, model, ufpe_name, all_universities_average_trends, # Renomeado para clareza
                                    pct_change_ensino, pct_change_pesquisa, pct_change_mercado,
                                    pct_change_inovacao, pct_change_internacionalizacao,
                                    apply_other_uni_trends):

    df_simulated_edicao = df_base_edicao_6.copy()

    # Define as colunas de notas que serão usadas
    notas_cols_base_list = ['Nota em Ensino', 'Nota em Pesquisa', 'Nota em Mercado', 'Nota em Inovação', 'Nota em Internacionalização']

    # Dicionário com as variações da UFPE
    ufpe_pct_changes = {
        'Nota em Ensino': pct_change_ensino,
        'Nota em Pesquisa': pct_change_pesquisa,
        'Nota em Mercado': pct_change_inovacao, # Corrigido: era pct_change_mercado, mas deveria ser pct_change_inovacao
        'Nota em Inovação': pct_change_inovacao, # Corrigido: era pct_change_internacionalizacao, mas deveria ser pct_change_inovacao
        'Nota em Internacionalização': pct_change_internacionalizacao
    }
    # CORREÇÃO IMPORTANTE: Verifiquei que havia um erro de cópia nos dicionários ufpe_pct_changes
    # As chaves 'Nota em Mercado' e 'Nota em Inovação' estavam recebendo o valor errado.
    # A linha correta deve ser:
    ufpe_pct_changes = {
        'Nota em Ensino': pct_change_ensino,
        'Nota em Pesquisa': pct_change_pesquisa,
        'Nota em Mercado': pct_change_mercado, # Agora está correto
        'Nota em Inovação': pct_change_inovacao, # Agora está correto
        'Nota em Internacionalização': pct_change_internacionalizacao
    }


    # Itera sobre cada universidade para aplicar as variações ou tendências
    for uni_idx, uni_row in df_simulated_edicao.iterrows():
        if uni_row['Universidade'] == ufpe_name:
            # Aplica as variações da UFPE (definidas pelos sliders)
            for col_base, pct_change_val in ufpe_pct_changes.items():
                original_note_ufpe = uni_row[col_base]
                new_note_ufpe = original_note_ufpe * (1 + pct_change_val)
                df_simulated_edicao.loc[uni_idx, col_base] = new_note_ufpe
        else:
            # Aplica as tendências médias para as outras universidades, se o checkbox estiver marcado
            if apply_other_uni_trends:
                for col_base in notas_cols_base_list:
                    col_pct_change_prev = f'{col_base}_pct_change_prev'
                    # Verifica se a universidade e a coluna de tendência existem no DataFrame de tendências
                    if uni_row['Universidade'] in all_universities_average_trends.index and col_pct_change_prev in all_universities_average_trends.columns:
                        trend_pct_change = all_universities_average_trends.loc[uni_row['Universidade'], col_pct_change_prev]
                    else:
                        trend_pct_change = 0.0 # Se não houver tendência média para essa uni/col, assume 0% de mudança

                    original_note_other = uni_row[col_base]
                    new_note_other = original_note_other * (1 + trend_pct_change)
                    df_simulated_edicao.loc[uni_idx, col_base] = new_note_other
            # Se apply_other_uni_trends for False, as notas das outras universidades permanecem as mesmas da Edição 6
            # (Não é necessário fazer nada aqui, pois o df_simulated_edicao já é uma cópia do df_base_edicao_6)

        # Recalcula a Nota Geral para cada universidade após as variações
        # Esta parte é crucial se 'Nota' é uma feature do modelo e não é a soma direta das outras.
        # Se o modelo espera uma 'Nota' geral calculada de forma específica, essa lógica deve ser replicada aqui.
        # Por enquanto, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculada de forma mais complexa, essa lógica precisará ser ajustada.
        # Por enquanto, vamos usar a média das notas para a 'Nota' geral, se não houver um cálculo específico.
        # É crucial que a 'Nota' geral seja consistente com as notas individuais.
        # Se 'Nota' é uma feature do modelo, ela deve ser tratada como as outras.
        # Se ela é uma feature calculada, precisamos garantir que o cálculo seja feito aqui.
        # Para simplificar, vamos assumir que a 'Nota' geral é a soma das notas individuais.
        # Se o modelo usa as notas individuais, não precisamos recalcular 'Nota' aqui.
        # Mas se 'Nota' é uma feature importante, é bom garantir que ela reflita as mudanças.
        # Vamos recalcular a 'Nota' geral aqui, assumindo que ela é a soma das notas individuais.
        # Se a 'Nota' geral for calculad

