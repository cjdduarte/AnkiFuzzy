from aqt import mw
from aqt.utils import showInfo, askUser
from aqt.qt import QAction, QProgressBar, QVBoxLayout, QDialog, QLabel, QApplication, QPushButton, QHBoxLayout, QLocale
from bs4 import BeautifulSoup
from . import fuzz  # Agora usa rapidfuzz diretamente
import time

# Importa condicionalmente do PyQt5 ou PyQt6
try:
    from PyQt5.QtCore import Qt  # Tentativa de importar do PyQt5
    application_modal = Qt.ApplicationModal
except ImportError:
    from PyQt6.QtCore import Qt  # Se falhar, importar do PyQt6
    application_modal = Qt.WindowModality.ApplicationModal  # Acesso ao ApplicationModal em PyQt6

#-------------Configuration------------------
config = mw.addonManager.getConfig(__name__)
FIELDS_TO_CHECK = config['FIELDS_TO_CHECK']
GROUP_SIZE = config.get('GROUP_SIZE', 40)  # Valor padrão 40 caso não esteja definido no config.json
#-------------Configuration------------------

# Verifica o idioma do sistema
current_language = QLocale().name()

# Define as traduções para os textos em inglês ou português
if current_language == "pt_BR":
    # Textos em português
    msg_deck_selected = "O deck selecionado é: {deck}.\nOs campos a serem verificados são: {fields}.\n\nDeseja continuar com a análise?"
    msg_cancelled = "Operação cancelada. Selecione outro deck para análise."
    msg_processing = "Processando cartões no deck: {deck}..."
    msg_cancel_button = "Cancelar"
    msg_process_cancelled = "Processo cancelado pelo usuário."
    msg_no_cards_found = "Nenhum cartão encontrado no deck atual."
    msg_no_fields_found = "Nenhum dos campos definidos ({fields}) foi encontrado nos cartões do deck."
    msg_analysis_complete = "{n} cartão(ões) semelhantes encontrados e {m} cartão(ões) foram marcados com tags em {tempo:.2f} segundos."
    msg_clear_tags_complete = "Todas as tags relacionadas ao AnkiFuzzy foram removidas."
    msg_confirm_clear_tags = "Tem certeza de que deseja remover todas as tags AnkiFuzzy?"
    tag_identical = "AnkiFuzzy::2-Análise::1-Idênticos"
    tag_similar = "AnkiFuzzy::2-Análise::2-Similares"
    tag_confirm = "AnkiFuzzy::2-Análise::3-Confirmar"
    tag_suspend = "AnkiFuzzy::1-Suspender"
    menu_label_locate = "1 - Localizar Cartões Semelhantes"
    menu_label_clear = "2 - Limpar Tags"
    menu_parent_label = "AnkiFuzzy"
else:
    # Textos em inglês
    msg_deck_selected = "The selected deck is: {deck}.\nThe fields to be checked are: {fields}.\n\nDo you want to continue with the analysis?"
    msg_cancelled = "Operation canceled. Please select another deck for analysis."
    msg_processing = "Processing cards in the deck: {deck}..."
    msg_cancel_button = "Cancel"
    msg_process_cancelled = "Process canceled by the user."
    msg_no_cards_found = "No cards found in the current deck."
    msg_no_fields_found = "None of the defined fields ({fields}) were found in the cards of the deck."
    msg_analysis_complete = "{n} similar cards found and {m} cards were tagged in {tempo:.2f} seconds."
    msg_clear_tags_complete = "All AnkiFuzzy-related tags have been removed."
    msg_confirm_clear_tags = "Are you sure you want to remove all AnkiFuzzy tags?"
    tag_identical = "AnkiFuzzy::2-Analysis::1-Identical"
    tag_similar = "AnkiFuzzy::2-Analysis::2-Similar"
    tag_confirm = "AnkiFuzzy::2-Analysis::3-Confirm"
    tag_suspend = "AnkiFuzzy::1-Suspend"
    menu_label_locate = "1 - Locate Similar Cards"
    menu_label_clear = "2 - Clear Tags"
    menu_parent_label = "AnkiFuzzy"

# Função para limpar o conteúdo HTML de um texto
def clean_html(text):
    return BeautifulSoup(text, "html.parser").get_text()

# Função otimizada para remover todas as tags relacionadas ao AnkiFuzzy
def clear_tags():
    if askUser(msg_confirm_clear_tags):
        ankifuzzy_prefix = "AnkiFuzzy"

        # Encontra apenas as notas que possuem tags que começam com "AnkiFuzzy"
        notes_with_ankifuzzy = mw.col.find_notes("tag:AnkiFuzzy*")

        for note_id in notes_with_ankifuzzy:
            note = mw.col.get_note(note_id)
            original_tags = note.tags

            # Filtra as tags que começam com "AnkiFuzzy"
            updated_tags = [tag for tag in original_tags if not tag.startswith(ankifuzzy_prefix)]

            # Se houve alteração, atualize as tags da nota
            if len(updated_tags) != len(original_tags):
                note.tags = updated_tags
                note.flush()  # Salva as alterações na nota

        # Recarrega as tags para garantir que o painel seja atualizado
        mw.col.tags.registerNotes(mw.col)  # Atualiza a lista de tags
        mw.reset()  # Atualiza a interface do Anki
        showInfo(msg_clear_tags_complete)





# Função principal para encontrar e marcar cartões semelhantes
def find_similar_cards():
    # Obtenha o deck atualmente selecionado
    current_deck = mw.col.decks.current()['name']
    
    # Pergunta ao usuário se deseja continuar com a análise no deck selecionado, informando os campos que serão analisados
    if not askUser(msg_deck_selected.format(deck=current_deck, fields=", ".join(FIELDS_TO_CHECK))):
        showInfo(msg_cancelled)
        return

    # Cria uma janela de diálogo para exibir a barra de progresso e o botão cancelar
    dialog = QDialog(mw)
    dialog.setWindowTitle("Progress" if current_language != "pt_BR" else "Progresso")

    # Torna a janela de diálogo modal
    dialog.setWindowModality(application_modal)  # Agora com suporte tanto para PyQt5 quanto PyQt6

    layout = QVBoxLayout(dialog)
    label = QLabel(msg_processing.format(deck=current_deck), dialog)
    layout.addWidget(label)
    
    progress_bar = QProgressBar(dialog)
    layout.addWidget(progress_bar)

    # Adicionar botão "Cancelar"
    cancel_button = QPushButton(msg_cancel_button, dialog)
    cancel_layout = QHBoxLayout()
    cancel_layout.addWidget(cancel_button)
    layout.addLayout(cancel_layout)

    dialog.setLayout(layout)
    dialog.setMinimumWidth(400)

    # Variável para controle de cancelamento
    is_canceled = [False]  # Usamos lista para que possa ser modificada dentro da função

    def cancel_processing():
        is_canceled[0] = True
        showInfo(msg_process_cancelled)
        dialog.reject()

    cancel_button.clicked.connect(cancel_processing)
    dialog.show()

    # Busca todos os cartões não suspensos no deck atual
    notes = mw.col.find_notes('deck:current -is:suspended')
    if not notes:
        showInfo(msg_no_cards_found)
        dialog.reject()  # Fecha o diálogo de progresso
        return

    # Dicionário para armazenar os textos dos cartões e seus IDs
    note_texts = {}

    # Extrai o conteúdo dos campos definidos na variável FIELDS_TO_CHECK
    found_any_field = False
    for note_id in notes:
        note = mw.col.get_note(note_id)
        for field_name in FIELDS_TO_CHECK:
            if field_name in note and note[field_name].strip():
                note_texts[note_id] = clean_html(note[field_name])
                found_any_field = True
                break

    # Verifica se pelo menos um campo foi encontrado
    if not found_any_field:
        showInfo(msg_no_fields_found.format(fields=", ".join(FIELDS_TO_CHECK)))
        dialog.reject()  # Fecha o diálogo de progresso
        return

    similar_cards = []
    note_ids = list(note_texts.keys())

    # Definindo os parâmetros para identificação de cartões semelhantes
    threshold_token_sort_ratio = 60  # Ajustar para ser mais permissivo
    threshold_partial_ratio = 85     # Ajustar para capturar mais variações

    start_time = time.time()
    total = len(note_ids)
    progress_bar.setMaximum(total)

    idNoteAddTagSimilar = []
    idNoteAddTagVerific = []
    nCartoesSimilares = 0

    # Agrupa os cartões por tamanho aproximado de texto
    note_groups = {}
    for note_id, text in note_texts.items():
        text_length_group = len(text) // GROUP_SIZE  # Usa o GROUP_SIZE do config.json
        if text_length_group not in note_groups:
            note_groups[text_length_group] = []
        note_groups[text_length_group].append(note_id)

    # Contagem total de comparações para a barra de progresso
    total_comparisons = sum(len(group) * (len(group) - 1) // 2 for group in note_groups.values())
    total_comparisons += sum(len(note_groups[group_key]) * len(note_groups[group_key + 1]) for group_key in note_groups if (group_key + 1) in note_groups)
    comparison_count = 0
    progress_bar.setMaximum(total_comparisons)  # Atualiza para o total de comparações possíveis

    # Compara cartões dentro do mesmo grupo e com os grupos vizinhos
    processed_pairs = set()  # Para evitar comparações duplicadas
    group_keys = sorted(note_groups.keys())

    for idx, group_key in enumerate(group_keys):
        if is_canceled[0]:
            break  # Se cancelado, interrompe o processamento
        
        # Compara dentro do grupo atual
        group = note_groups[group_key]
        for i, note_id1 in enumerate(group):
            current_Card = {'noteId': note_id1, 'texto': note_texts[note_id1]}
            for note_id2 in group[i + 1:]:
                if is_canceled[0]:
                    break  # Se cancelado, interrompe o processamento
                compare_Card = {'noteId': note_id2, 'texto': note_texts[note_id2]}

                pair = tuple(sorted((note_id1, note_id2)))
                if pair not in processed_pairs:
                    processed_pairs.add(pair)
                    comparison_count += 1

                    # Evita comparar um cartão consigo mesmo
                    nota_original = current_Card['texto']
                    nota_comparacao = compare_Card['texto']

                    highest3 = fuzz.token_sort_ratio(nota_original, nota_comparacao)
                    if highest3 >= 70:
                        highest2 = fuzz.partial_ratio(nota_original.encode('utf-8'), nota_comparacao.encode('utf-8'))
                        if highest2 >= 97 or highest3 >= 88 or (highest3 >= 85 and highest2 >= 85):
                            idNoteAddTagSimilar.append(compare_Card['noteId'])
                            idNoteAddTagVerific.append([current_Card['noteId'], compare_Card['noteId'], highest3, highest2])
                            nCartoesSimilares += 1
                    
                    progress_bar.setValue(comparison_count)
                    QApplication.processEvents()

        # Comparar com o grupo vizinho
        if idx < len(group_keys) - 1:
            next_group_key = group_keys[idx + 1]
            next_group = note_groups[next_group_key]
            for note_id1 in group:
                current_Card = {'noteId': note_id1, 'texto': note_texts[note_id1]}
                for note_id2 in next_group:
                    if is_canceled[0]:
                        break

                    compare_Card = {'noteId': note_id2, 'texto': note_texts[note_id2]}

                    pair = tuple(sorted((note_id1, note_id2)))
                    if pair not in processed_pairs:
                        processed_pairs.add(pair)
                        comparison_count += 1

                        nota_original = current_Card['texto']
                        nota_comparacao = compare_Card['texto']

                        highest3 = fuzz.token_sort_ratio(nota_original, nota_comparacao)
                        if highest3 >= 70:
                            highest2 = fuzz.partial_ratio(nota_original.encode('utf-8'), nota_comparacao.encode('utf-8'))
                            if highest2 >= 97 or highest3 >= 88 or (highest3 >= 85 and highest2 >= 85):
                                idNoteAddTagSimilar.append(compare_Card['noteId'])
                                idNoteAddTagVerific.append([current_Card['noteId'], compare_Card['noteId'], highest3, highest2])
                                nCartoesSimilares += 1
                    
                        progress_bar.setValue(comparison_count)
                        QApplication.processEvents()

    if not is_canceled[0]:
        # Adiciona as tags com base nos valores de similaridade
        for note_id1, note_id2, highest3, highest2 in idNoteAddTagVerific:
            idTag = [note_id1, note_id2]
            if highest3 >= 95 and highest2 >= 98:
                mw.col.tags.bulkAdd(idTag, f"{tag_identical}::{note_id1}")
            elif highest3 >= 95 or highest2 >= 94:
                mw.col.tags.bulkAdd(idTag, f"{tag_similar}::{note_id1}")
            else:
                mw.col.tags.bulkAdd(idTag, f"{tag_confirm}::{note_id1}")

        idNoteAddTagSimilar = list(set(idNoteAddTagSimilar))
        if idNoteAddTagSimilar:
            mw.col.tags.bulkAdd(idNoteAddTagSimilar, tag_suspend)

        elapsed_time = time.time() - start_time
        showInfo(msg_analysis_complete.format(n=nCartoesSimilares, m=len(idNoteAddTagVerific), tempo=elapsed_time))
    
    dialog.accept()
    mw.reset()

# Função para adicionar itens de menu no Anki
def add_menu_item():
    # Adiciona o menu principal "Anki AnkiFuzzy"
    parent_menu = mw.form.menuTools.addMenu(menu_parent_label)

    # Submenu para localizar cartões semelhantes
    locate_action = QAction(menu_label_locate, mw)
    locate_action.triggered.connect(find_similar_cards)
    parent_menu.addAction(locate_action)

    # Submenu para limpar tags
    clear_action = QAction(menu_label_clear, mw)
    clear_action.triggered.connect(clear_tags)
    parent_menu.addAction(clear_action)

add_menu_item()
