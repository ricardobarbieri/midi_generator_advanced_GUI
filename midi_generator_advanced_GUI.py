# Importações de bibliotecas necessárias
import tkinter as tk                         # Biblioteca para criar interfaces gráficas
from tkinter import ttk, messagebox          # Componentes adicionais do tkinter
import ttkbootstrap as ttkb                  # Versão estilizada do ttk
from ttkbootstrap.constants import *         # Constantes para estilos do ttkbootstrap
import mido                                  # Biblioteca para manipulação de MIDI
from mido import MidiFile, MidiTrack, Message, MetaMessage  # Classes específicas para MIDI
import random                                # Para geração aleatória

# Definição dos nomes das notas musicais (escala cromática)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# Cria um dicionário para mapear nomes de notas para seus índices numéricos
BASE_NOTES = {name: i for i, name in enumerate(NOTE_NAMES)}

# Definição dos modos musicais e seus intervalos em semitons
# Cada lista representa os intervalos entre notas consecutivas da escala
MODES = {
    'Major (Ionian)': [2, 2, 1, 2, 2, 2, 1],      # Escala maior (jônica)
    'Minor (Aeolian)': [2, 1, 2, 2, 1, 2, 2],     # Escala menor natural (eólia)
    'Dorian': [2, 1, 2, 2, 2, 1, 2],              # Modo dórico
    'Phrygian': [1, 2, 2, 2, 1, 2, 2],            # Modo frígio
    'Lydian': [2, 2, 2, 1, 2, 2, 1],              # Modo lídio
    'Mixolydian': [2, 2, 1, 2, 2, 1, 2],          # Modo mixolídio
    'Locrian': [1, 2, 2, 1, 2, 2, 2]              # Modo lócrio
}

# Opções predefinidas para estruturas de música
STRUCTURE_OPTIONS = [
    'Intro-Verse-Chorus-Verse-Chorus-Bridge-Chorus-Outro',  # Estrutura completa
    'Verse-Chorus-Verse-Chorus-Bridge-Chorus',              # Estrutura sem intro/outro
    'Intro-Verse-Chorus-Outro'                              # Estrutura simplificada
]

# Círculo de quintas, usado para sugestões harmônicas
# Os números representam os índices das notas em NOTE_NAMES
CIRCLE_OF_FIFTHS = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]  # C, G, D, A, E, B, F#, C#, G#, D#, A#, F

# Função para encontrar sugestões harmônicas baseadas no círculo de quintas
def get_harmonic_suggestions(current_note_name, mode):
    # Encontra o índice da nota atual no círculo de quintas
    current_note_idx = BASE_NOTES[current_note_name]
    circle_idx = CIRCLE_OF_FIFTHS.index(current_note_idx)
    
    # Gera sugestões de notas próximas no círculo de quintas
    suggestions = []
    for offset in [-1, 1, -2, 2]:  # Verifica notas adjacentes e próximas no círculo
        suggestion_idx = (circle_idx + offset) % 12
        suggestion_note = NOTE_NAMES[CIRCLE_OF_FIFTHS[suggestion_idx]]
        # Sugere o modo mais comum baseado no modo atual
        suggested_mode = 'Major (Ionian)' if 'Major' in mode or 'Lydian' in mode or 'Mixolydian' in mode else 'Minor (Aeolian)'
        suggestions.append(f"{suggestion_note} ({suggested_mode})")
    
    return suggestions

# Função para gerar uma escala musical com base na nota raiz e modo
def generate_scale(root_note, mode):
    intervals = MODES[mode]
    scale = [root_note]  # Começa com a nota raiz
    current_note = root_note
    # Aplica os intervalos sequencialmente para construir a escala
    for interval in intervals[:-1]:  # Não precisamos do último intervalo porque ele retorna à nota raiz
        current_note += interval
        scale.append(current_note)
    return scale

# Função para gerar uma melodia simples usando notas da escala
def generate_melody(scale, length_in_beats):
    melody = []
    for i in range(length_in_beats):
        # Seleciona notas ciclicamente, subindo oitavas quando necessário
        note = scale[i % len(scale)] + (12 * (i // len(scale)))
        # Cria evento de nota com duração e velocidade padrão
        melody.append({'note': note, 'duration': 480, 'velocity': 100})  # 480 ticks = 1 beat em MIDI
    return melody

# Função principal para gerar o arquivo MIDI
def generate_midi_file(bpm, section_notes, section_modes, section_lengths, structure):
    mid = MidiFile()  # Cria um novo arquivo MIDI
    track = MidiTrack()  # Cria uma trilha MIDI
    mid.tracks.append(track)  # Adiciona a trilha ao arquivo

    # Define o tempo (BPM)
    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))

    # Divide a estrutura em seções
    sections = structure.split('-')

    # Itera por cada seção da música
    for i, section in enumerate(sections):
        # Obtém configurações para esta seção
        root_note_name = section_notes[i]
        mode = section_modes[i]
        # Converte nome da nota para valor MIDI (60 = C4, oitava central)
        root_note = BASE_NOTES[root_note_name] + 60
        section_length = section_lengths[i]

        # Gera a escala e a melodia para a seção
        scale = generate_scale(root_note, mode)
        melody = generate_melody(scale, section_length)
        
        # Adiciona eventos de nota MIDI (note_on e note_off)
        for note_event in melody:
            # Nota ligada (começa a tocar)
            track.append(Message('note_on', note=note_event['note'], 
                         velocity=note_event['velocity'], time=0))
            # Nota desligada (termina de tocar após a duração)
            track.append(Message('note_off', note=note_event['note'], 
                         velocity=0, time=note_event['duration']))

    # Cria nome de arquivo baseado nas configurações
    filename = f"song_{section_notes[0]}_{section_modes[0]}_{bpm}bpm.mid".replace(" ", "_").replace("#", "sharp")
    # Salva o arquivo MIDI
    mid.save(filename)
    return filename

# Classe principal da aplicação GUI
class MidiGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Music Generator")
        self.root.geometry("600x500")  # Define tamanho da janela

        # Aplica tema escuro com ttkbootstrap
        style = ttkb.Style(theme='darkly')

        # Cria um canvas com barra de rolagem para acomodar muitas seções
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttkb.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttkb.Frame(self.canvas)

        # Configura eventos de rolagem
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Posiciona elementos de rolagem
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Frame principal que conterá todos os widgets
        self.main_frame = ttkb.Frame(self.scrollable_frame, padding=10)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Título do aplicativo
        self.title_label = ttkb.Label(self.main_frame, text="MIDI Music Generator", 
                                      font=("Helvetica", 16, "bold"), bootstyle="primary")
        self.title_label.pack(pady=5)

        # Frame para configurações gerais da música
        self.settings_frame = ttkb.LabelFrame(self.main_frame, text="General Settings", 
                                            padding=5, bootstyle="info")
        self.settings_frame.pack(fill=X, pady=5)

        # Campo para BPM (andamento)
        self.bpm_label = ttkb.Label(self.settings_frame, text="BPM:", font=("Helvetica", 10))
        self.bpm_label.grid(row=0, column=0, padx=5, pady=2, sticky=W)
        self.bpm_var = tk.StringVar(value="120")  # Valor padrão
        self.bpm_entry = ttkb.Entry(self.settings_frame, textvariable=self.bpm_var, 
                                  bootstyle="primary", width=10)
        self.bpm_entry.grid(row=0, column=1, padx=5, pady=2)

        # Dropdown para estrutura musical
        self.structure_label = ttkb.Label(self.settings_frame, text="Structure:", font=("Helvetica", 10))
        self.structure_label.grid(row=1, column=0, padx=5, pady=2, sticky=W)
        self.structure_var = tk.StringVar(value=STRUCTURE_OPTIONS[0])
        self.structure_menu = ttkb.Combobox(self.settings_frame, textvariable=self.structure_var, 
                                          values=STRUCTURE_OPTIONS, state="readonly", 
                                          bootstyle="primary", width=30)
        self.structure_menu.grid(row=1, column=1, padx=5, pady=2)
        # Atualiza configuração de seções quando a estrutura muda
        self.structure_menu.bind("<<ComboboxSelected>>", self.update_section_config)

        # Checkbox para notas aleatórias
        self.random_notes_var = tk.BooleanVar(value=False)
        self.random_notes_check = ttkb.Checkbutton(self.settings_frame, text="Random Notes", 
                                                variable=self.random_notes_var, 
                                                bootstyle="primary", 
                                                command=self.update_section_config)
        self.random_notes_check.grid(row=2, column=0, columnspan=2, pady=2)

        # Frame para configurações de cada seção da música
        self.sections_frame = ttkb.LabelFrame(self.main_frame, text="Section Settings", 
                                            padding=5, bootstyle="info")
        self.sections_frame.pack(fill=X, pady=5)

        # Listas para armazenar variáveis de cada seção
        self.section_note_vars = []     # Notas base
        self.section_mode_vars = []     # Modos (escalas)
        self.section_length_vars = []   # Durações

        # Frame para mostrar sugestões harmônicas
        self.harmony_frame = ttkb.LabelFrame(self.main_frame, text="Harmonic Suggestions", 
                                           padding=5, bootstyle="warning")
        self.harmony_frame.pack(fill=X, pady=5)
        self.harmony_label = ttkb.Label(self.harmony_frame, 
                                      text="Select a section to see harmonic suggestions", 
                                      font=("Helvetica", 10), bootstyle="warning", 
                                      wraplength=500)
        self.harmony_label.pack()

        # Botão para gerar o arquivo MIDI
        self.generate_button = ttkb.Button(self.main_frame, text="Generate MIDI", 
                                         command=self.generate_midi, 
                                         bootstyle="success-outline")
        self.generate_button.pack(pady=10)

        # Label para mostrar status da operação
        self.status_label = ttkb.Label(self.main_frame, text="Ready to generate...", 
                                     font=("Helvetica", 10), bootstyle="info")
        self.status_label.pack(pady=5)

        # Inicializa campos das seções
        self.update_section_config()

    # Método para atualizar a interface com base na estrutura musical selecionada
    def update_section_config(self, event=None):
        # Remove campos de seção anteriores
        for widget in self.sections_frame.winfo_children():
            widget.destroy()
        self.section_note_vars.clear()
        self.section_mode_vars.clear()
        self.section_length_vars.clear()

        # Obtém estrutura atual e status do modo aleatório
        structure = self.structure_var.get()
        sections = structure.split('-')
        use_random = self.random_notes_var.get()

        # Cria campos para cada seção da estrutura musical
        for i, section in enumerate(sections):
            # Nome da seção (Intro, Verse, etc.)
            ttkb.Label(self.sections_frame, text=f"{section}:", 
                     font=("Helvetica", 10)).grid(row=i, column=0, padx=5, pady=2, sticky=W)

            # Seleção de nota base (ou label "Random" se modo aleatório)
            note_var = tk.StringVar(value="C")
            if use_random:
                note_menu = ttkb.Label(self.sections_frame, text="Random", 
                                    font=("Helvetica", 10), bootstyle="secondary")
            else:
                note_menu = ttkb.Combobox(self.sections_frame, textvariable=note_var, 
                                        values=NOTE_NAMES, state="readonly", 
                                        bootstyle="primary", width=10)
            note_menu.grid(row=i, column=1, padx=5, pady=2)
            self.section_note_vars.append(note_var)

            # Seleção de modo (escala)
            mode_var = tk.StringVar(value="Major (Ionian)")
            mode_menu = ttkb.Combobox(self.sections_frame, textvariable=mode_var, 
                                    values=list(MODES.keys()), state="readonly", 
                                    bootstyle="primary", width=15)
            mode_menu.grid(row=i, column=2, padx=5, pady=2)
            self.section_mode_vars.append(mode_var)

            # Campo para duração da seção
            length_var = tk.StringVar(value="8")
            length_entry = ttkb.Entry(self.sections_frame, textvariable=length_var, 
                                    bootstyle="primary", width=5)
            length_entry.grid(row=i, column=3, padx=5, pady=2)
            self.section_length_vars.append(length_var)

            # Configura eventos para atualizar sugestões harmônicas
            note_menu.bind("<<ComboboxSelected>>", 
                          lambda event, idx=i: self.update_harmony_suggestions(idx))
            mode_menu.bind("<<ComboboxSelected>>", 
                          lambda event, idx=i: self.update_harmony_suggestions(idx))

        # Atualiza sugestões para a primeira seção
        self.update_harmony_suggestions(0)

    # Método para atualizar as sugestões harmônicas baseadas na seção selecionada
    def update_harmony_suggestions(self, current_section_idx):
        if current_section_idx == 0:
            # Para a primeira seção não há sugestões (não há seção anterior)
            self.harmony_label.config(text="First section: No previous section to base suggestions on.")
            return

        # Obtém dados da seção anterior para gerar sugestões
        prev_note = self.section_note_vars[current_section_idx - 1].get()
        prev_mode = self.section_mode_vars[current_section_idx - 1].get()

        # Gera e mostra sugestões harmônicas
        suggestions = get_harmonic_suggestions(prev_note, prev_mode)
        suggestion_text = f"Suggestions for {self.structure_var.get().split('-')[current_section_idx]} (based on {prev_note} {prev_mode}):\n"
        suggestion_text += ", ".join(suggestions)
        self.harmony_label.config(text=suggestion_text)

    # Método para gerar o arquivo MIDI final
    def generate_midi(self):
        try:
            # Obtém valores dos campos
            bpm = int(self.bpm_var.get())
            structure = self.structure_var.get()
            use_random = self.random_notes_var.get()

            # Validação do BPM
            if bpm < 20 or bpm > 300:
                raise ValueError("BPM must be between 20 and 300.")

            # Inicializa as listas para dados das seções
            section_notes = []
            section_modes = [mode_var.get() for mode_var in self.section_mode_vars]
            section_lengths = []

            # Valida e obtém as durações das seções
            for length_var in self.section_length_vars:
                length = int(length_var.get())
                if length < 1 or length > 32:
                    raise ValueError("Section length must be between 1 and 32 beats.")
                section_lengths.append(length)

            # Processa as notas para cada seção
            sections = structure.split('-')
            for i in range(len(sections)):
                if use_random and i > 0:  # Primeira seção sempre usa nota fixa
                    # Seleciona aleatoriamente uma das sugestões harmônicas
                    prev_note = section_notes[i - 1]
                    suggestions = get_harmonic_suggestions(prev_note, section_modes[i - 1])
                    suggested_notes = [s.split()[0] for s in suggestions]  # Extrai apenas a nota
                    chosen_note = random.choice(suggested_notes)
                    section_notes.append(chosen_note)
                else:
                    # Usa a nota selecionada pelo usuário
                    section_notes.append(self.section_note_vars[i].get())

            # Gera o arquivo MIDI
            filename = generate_midi_file(bpm, section_notes, section_modes, section_lengths, structure)
            
            # Atualiza interface com status de sucesso
            self.status_label.config(text=f"MIDI file generated: {filename}", bootstyle="success")
            messagebox.showinfo("Success", f"MIDI file '{filename}' generated successfully! Import it into FL Studio.")

        except ValueError as e:
            # Tratamento de erros de validação
            self.status_label.config(text=str(e), bootstyle="danger")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            # Tratamento de outros erros
            self.status_label.config(text="Error generating MIDI file", bootstyle="danger")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Ponto de entrada do programa
if __name__ == "__main__":
    root = ttkb.Window()  # Cria janela principal com ttkbootstrap
    app = MidiGeneratorApp(root)  # Inicializa a aplicação
    root.mainloop()  # Inicia o loop de eventos da interface