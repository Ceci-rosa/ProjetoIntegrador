import customtkinter as ctk
import mysql.connector
import tkinter as tk
from tkinter import messagebox
from PIL import Image
import bcrypt  

# ================== CONEXÃO COM BD ==================
try:
    bd = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="comanda_facil"
    )
    cursor = bd.cursor()
    print("Conexão com BD estabelecida com sucesso!")
except mysql.connector.Error as e:
    print(f"Erro de BD: {e}")
    exit()

# ================== CONFIGURAÇÃO DA JANELA ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

janela = ctk.CTk()
janela.geometry("1400x900")
janela.title("ComandaFácil")
janela.rowconfigure(0, weight=1)
janela.columnconfigure(0, weight=1)

# ================== VARIÁVEIS GLOBAIS ==================
id_usuario_logado = None
frame_mesas = None
frame_status = None
frame_historico = None

# ================== FUNÇÕES PRINCIPAIS ==================
def mostrartela(tela):
    tela.tkraise()

def logout():
    global id_usuario_logado
    id_usuario_logado = None
    mostrartela(telabemvindo)

def cadastrar():
    nome = entrada_nome.get()
    cpf = entrada_cpf.get()
    senha = entrada_senha.get()

    if not nome or not cpf or not senha:
        mensagem_cadastro.configure(text="Preencha todos os campos.")
        return

    if not senha.isalnum() or len(senha) != 6:
        mensagem_cadastro.configure(text="A senha deve ter exatamente 6 caracteres alfanuméricos.")
        return

    # Verificar se CPF já existe
    cursor.execute("SELECT cpf FROM cadastro WHERE cpf = %s", (cpf,))
    if cursor.fetchone():
        mensagem_cadastro.configure(text="CPF já cadastrado.")
        return

    # Hash da senha
    hashed_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute("INSERT INTO cadastro (nome, cpf, senha) VALUES (%s, %s, %s)", (nome, cpf, hashed_senha.decode('utf-8')))
        bd.commit()
        mensagem_cadastro.configure(text="Cadastro realizado com sucesso.")
        entrada_nome.delete(0, "end")
        entrada_cpf.delete(0, "end")
        entrada_senha.delete(0, "end")
        telacadastro.after(2000, lambda: mostrartela(telalogin))
    except mysql.connector.Error as e:
        mensagem_cadastro.configure(text=f"Erro ao cadastrar: {e}")

def logar():
    global id_usuario_logado
    cpf = entrada_login_cpf.get()
    senha = entrada_login_senha.get()

    if not cpf or not senha:
        mensagem_login.configure(text="Preencha os campos.")
        return

    cursor.execute("SELECT id_usuario, senha FROM cadastro WHERE cpf = %s", (cpf,))
    resultado = cursor.fetchone()

    if resultado:
        id_usuario_logado = resultado[0]
        senha_bd = resultado[1]
        if bcrypt.checkpw(senha.encode('utf-8'), senha_bd.encode('utf-8')):
            mensagem_login.configure(text="Login realizado!")
            entrada_login_cpf.delete(0, "end")
            entrada_login_senha.delete(0, "end")
            configurar_tela_principal(janela, telaprincipal, telabemvindo)
            telalogin.after(1000, lambda: mostrartela(telaprincipal))
        else:
            mensagem_login.configure(text="Senha incorreta.")
    else:
        mensagem_login.configure(text="CPF não encontrado.")

# ================== MESAS ==================
def carregar_mesas():
    global frame_mesas
    for widget in frame_mesas.winfo_children():
        widget.destroy()

    ctk.CTkLabel(frame_mesas, text="🍽️ Tela de Mesas", font=("Arial", 24, "bold"), text_color="#FFFFFF", fg_color="#2E2E2E", corner_radius=10).pack(pady=20, fill="x", padx=10)

    try:
        cursor.execute("SELECT numero, em_uso FROM mesa")
        mesas = cursor.fetchall()

        if not mesas:
            ctk.CTkLabel(frame_mesas, text="Nenhuma mesa cadastrada. 😊", font=("Arial", 16), text_color="#CCCCCC", fg_color="#1E1E1E", corner_radius=10).pack(pady=10, padx=10, fill="x")
        else:
            for mesa in mesas:
                numero, em_uso = mesa
                status = "Ocupada" if em_uso else "Livre"
                cor_status = "#B50000" if em_uso else "#001A6E"  # Vermelho para ocupada, verde para livre
                
                frame_mesa = ctk.CTkFrame(frame_mesas, fg_color="#81A1C1", corner_radius=15)
                frame_mesa.pack(pady=10, fill="x", padx=20)
                
                ctk.CTkLabel(frame_mesa, text=f"🍴 Mesa {numero}", font=("Arial", 18, "bold"), text_color="#FFFFFF").pack(side="left", padx=10, pady=10)
                ctk.CTkLabel(frame_mesa, text=f"Status: {status}", font=("Arial", 14), text_color=cor_status).pack(side="left", padx=10, pady=10)
                
                # Botão Fazer Pedido sempre disponível
                ctk.CTkButton(frame_mesa, text="➕ Fazer Pedido", command=lambda m=numero: adicionar_pedido(m), fg_color="#4CAF50", hover_color="#45A049", width=120, height=40, corner_radius=8).pack(side="left", padx=5)
                
                # Botão Fechar Mesa só se ocupada
                if em_uso:
                    ctk.CTkButton(frame_mesa, text="💰 Fechar Mesa", command=lambda m=numero: fechar_mesa(m), fg_color="#2196F3", hover_color="#1976D2", width=120, height=40, corner_radius=8).pack(side="left", padx=5)

        ctk.CTkButton(frame_mesas, text="➕ Adicionar Mesa", command=adicionar_mesa, fg_color="#FF9800", hover_color="#F57C00", width=200, height=50, corner_radius=10).pack(pady=20)

    except mysql.connector.Error as e:
        ctk.CTkLabel(frame_mesas, text=f"❌ Erro ao carregar mesas: {e}", font=("Arial", 14), text_color="#FF6B6B", fg_color="#1E1E1E", corner_radius=10).pack(pady=10, padx=10, fill="x")

def adicionar_mesa():
    
    popup = ctk.CTkToplevel()
    popup.title("Adicionar Nova Mesa")
    popup.geometry("400x250")
    popup.resizable(False, False)
    popup.transient(janela)
    popup.grab_set()
    popup.configure(fg_color="#2E2E2E")

    ctk.CTkLabel(popup, text="➕ Adicionar Nova Mesa", font=("Arial", 20, "bold"), text_color="#FFFFFF").pack(pady=20)
    
    entrada_numero = ctk.CTkEntry(popup, placeholder_text="Número da mesa", width=300, height=40, corner_radius=8)
    entrada_numero.pack(pady=10)
    
    mensagem_popup = ctk.CTkLabel(popup, text="", font=("Arial", 12), text_color="#FF6B6B")
    mensagem_popup.pack(pady=5)

    def salvar_mesa():
        numero = entrada_numero.get()
        if not numero:
            mensagem_popup.configure(text="Digite o número da mesa.", text_color="#FF6B6B")
            return
        try:
            cursor.execute("INSERT INTO mesa (numero, em_uso) VALUES (%s, FALSE)", (numero,))
            bd.commit()
            mensagem_popup.configure(text="Mesa adicionada com sucesso!", text_color="#4CAF50")
            popup.after(2000, popup.destroy)
            carregar_mesas()
        except mysql.connector.Error as e:
            mensagem_popup.configure(text=f"Erro ao adicionar mesa: {e}", text_color="#FF6B6B")
        
    frame_botoes = ctk.CTkFrame(popup, fg_color="transparent")
    frame_botoes.pack(pady=10)
    ctk.CTkButton(frame_botoes, text="Salvar", command=salvar_mesa, fg_color="#4CAF50", hover_color="#45A049", width=100, height=40, corner_radius=8).pack(side="left", padx=10)
    ctk.CTkButton(frame_botoes, text="Cancelar", command=popup.destroy, fg_color="#F44336", hover_color="#D32F2F", width=100, height=40, corner_radius=8).pack(side="right", padx=10)

    
    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")


def fechar_mesa(mesa_numero):
    popup = ctk.CTkToplevel()
    popup.title(f"Fechar Mesa {mesa_numero}")
    popup.geometry("500x600")
    popup.resizable(False, False)
    popup.transient(janela)
    popup.grab_set()
    popup.configure(fg_color="#2E2E2E")

    ctk.CTkLabel(popup, text=f"💰 Fechar Mesa {mesa_numero}", font=("Arial", 22, "bold"), text_color="#FFFFFF").pack(pady=20)

    scrollable_frame = ctk.CTkScrollableFrame(popup, fg_color="#1E1E1E", corner_radius=10)
    scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

    try:
        # Mostrar apenas pedidos não fechados com a mesa (para evitar contas anteriores)
        cursor.execute("""
            SELECT p.id, p.status, p.valor_total, p.datahora, ip.item, ip.quantidade, ip.valor
            FROM pedido p 
            JOIN item_pedido ip ON p.id = ip.id_pedido
            WHERE p.idmesa = %s AND p.fechado_com_mesa = FALSE
            ORDER BY p.datahora DESC
        """, (mesa_numero,))
        pedidos = cursor.fetchall()

        if not pedidos:
            ctk.CTkLabel(scrollable_frame, text="Nenhum pedido em aberto para esta mesa. 😊", font=("Arial", 16), text_color="#CCCCCC").pack(pady=20)
            valor_total_mesa = 0.0
        else:
            pedidos_por_pedido = {}
            valor_total_mesa = 0.0
            for pedido in pedidos:
                id_pedido, status, valor_total, datahora, item, quantidade, valor = pedido
                if id_pedido not in pedidos_por_pedido:
                    pedidos_por_pedido[id_pedido] = {
                        'status': status,
                        'valor_total': 0.0,  # Inicializar como 0, será calculado abaixo
                        'datahora': datahora,
                        'itens': []
                    }
                # Calcular o valor total do pedido baseado nos itens (quantidade * valor)
                pedidos_por_pedido[id_pedido]['itens'].append(f"{item} ({quantidade}x R${valor:.2f})")
                pedidos_por_pedido[id_pedido]['valor_total'] += float(quantidade) * float(valor)
            
            # Agora somar o valor_total calculado de cada pedido para o total da mesa
            for detalhes in pedidos_por_pedido.values():
                valor_total_mesa += detalhes['valor_total']

            for id_pedido, detalhes in pedidos_por_pedido.items():
                cor_frame = "#4CAF50" if detalhes['status'] == 'finalizado' else "#FF9800"
                frame_pedido = ctk.CTkFrame(scrollable_frame, fg_color=cor_frame, corner_radius=10)
                frame_pedido.pack(pady=10, fill="x")
                ctk.CTkLabel(frame_pedido, text=f"📋 Pedido {id_pedido} ({detalhes['status']}) - {detalhes['datahora']}", font=("Arial", 16, "bold"), text_color="#FFFFFF").pack(pady=5)
                itens_str = ", ".join(detalhes['itens'])
                ctk.CTkLabel(frame_pedido, text=f"Itens: {itens_str}", font=("Arial", 12), text_color="#ECEFF4").pack(pady=5)
                ctk.CTkLabel(frame_pedido, text=f"Valor: R${detalhes['valor_total']:.2f}", font=("Arial", 14, "bold"), text_color="#A3BE8C").pack(pady=5)

        frame_total = ctk.CTkFrame(scrollable_frame, fg_color="#2196F3", corner_radius=10)
        frame_total.pack(pady=20, fill="x")
        ctk.CTkLabel(frame_total, text=f"💵 Valor Total da Mesa: R${valor_total_mesa:.2f}", font=("Arial", 18, "bold"), text_color="#FFFFFF").pack(pady=10)

    except mysql.connector.Error as e:
        ctk.CTkLabel(scrollable_frame, text=f"❌ Erro ao carregar conta: {e}", font=("Arial", 14), text_color="#FF6B6B").pack(pady=20)

    frame_botoes = ctk.CTkFrame(popup, fg_color="transparent")
    frame_botoes.pack(pady=10)

    def confirmar_fechamento():
        try:
            # Finalizar todos os pedidos em andamento da mesa que não estão fechados
            cursor.execute("UPDATE pedido SET status = 'finalizado' WHERE idmesa = %s AND status = 'em andamento' AND fechado_com_mesa = FALSE", (mesa_numero,))
            
            # Marcar todos os pedidos da mesa como fechados com a mesa (para não aparecerem mais)
            cursor.execute("UPDATE pedido SET fechado_com_mesa = TRUE WHERE idmesa = %s AND fechado_com_mesa = FALSE", (mesa_numero,))
            
            # Marcar mesa como não em uso
            cursor.execute("UPDATE mesa SET em_uso = FALSE WHERE numero = %s", (mesa_numero,))
            
            bd.commit()
            
            popup.destroy()
            carregar_mesas()  # Recarregar mesas
            carregar_status()  # Recarregar status
            carregar_historico()  # Recarregar histórico
            
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Falha ao fechar a mesa: {str(e)}")

    btn_confirmar = ctk.CTkButton(frame_botoes, text="Confirmar Fechamento", fg_color="#4CAF50", hover_color="#45A049", width=150, height=40, corner_radius=8, command=confirmar_fechamento)
    btn_confirmar.pack(side="left", padx=10)

    btn_fechar = ctk.CTkButton(frame_botoes, text="Cancelar", fg_color="#F44336", hover_color="#D32F2F", width=150, height=40, corner_radius=8, command=popup.destroy)
    btn_fechar.pack(side="right", padx=10)

    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")

def adicionar_pedido(mesa_numero):
    popup = ctk.CTkToplevel()
    popup.title(f"Novo Pedido - Mesa {mesa_numero}")
    popup.geometry("450x550")  
    popup.resizable(False, False)
    popup.transient(janela)  
    popup.grab_set() 

    popup.configure(fg_color="#2E2E2E")

    titulo = ctk.CTkLabel(popup, text=f"Novo Pedido - Mesa {mesa_numero}", font=("Arial", 20, "bold"), text_color="#FFFFFF")
    titulo.pack(pady=(20, 10))

    
    frame_campos = ctk.CTkFrame(popup, fg_color="#1E1E1E", corner_radius=10)
    frame_campos.pack(pady=10, padx=20, fill="both", expand=True)

    ctk.CTkLabel(frame_campos, text="Itens (separados por vírgula):", font=("Arial", 14), text_color="#CCCCCC").pack(anchor="w", padx=10, pady=(10, 5))
    entrada_itens = ctk.CTkEntry(frame_campos, placeholder_text="Ex: Pizza, Refrigerante, Sobremesa", width=350, height=40, corner_radius=8)
    entrada_itens.pack(pady=(0, 10), padx=10)

    ctk.CTkLabel(frame_campos, text="Quantidades (separadas por vírgula, uma por item):", font=("Arial", 14), text_color="#CCCCCC").pack(anchor="w", padx=10, pady=(10, 5))
    entrada_quantidades = ctk.CTkEntry(frame_campos, placeholder_text="Ex: 1, 2, 1", width=350, height=40, corner_radius=8)
    entrada_quantidades.pack(pady=(0, 10), padx=10)

    ctk.CTkLabel(frame_campos, text="Valores (R$, separados por vírgula, um por item):", font=("Arial", 14), text_color="#CCCCCC").pack(anchor="w", padx=10, pady=(10, 5))
    entrada_valores = ctk.CTkEntry(frame_campos, placeholder_text="Ex: 25.00, 10.00, 15.00", width=350, height=40, corner_radius=8)
    entrada_valores.pack(pady=(0, 10), padx=10)

    mensagem_popup = ctk.CTkLabel(frame_campos, text="", font=("Arial", 12), text_color="#FF6B6B")  # Vermelho para erros
    mensagem_popup.pack(pady=(5, 10))


    confirmando = [False]  
    valor_total_calculado = [0.0]  # Para armazenar o valor total calculado

    frame_botoes = ctk.CTkFrame(popup, fg_color="transparent")
    frame_botoes.pack(pady=(10, 20))

    btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar Pedido", fg_color="#4CAF50", hover_color="#45A049", width=150, height=40, corner_radius=8)
    btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", fg_color="#F44336", hover_color="#D32F2F", width=150, height=40, corner_radius=8)

    def voltar():
        confirmando[0] = False
        mensagem_popup.configure(text="", text_color="#FF6B6B")
        btn_salvar.configure(text="Salvar Pedido", command=salvar_pedido)
        btn_cancelar.configure(text="Cancelar", command=popup.destroy)

    def confirmar_salvamento():
        itens = entrada_itens.get().strip()
        quantidades = entrada_quantidades.get().strip()
        valores = entrada_valores.get().strip()

        itens_lista = [item.strip() for item in itens.split(",") if item.strip()]
        quantidades_lista = [q.strip() for q in quantidades.split(",") if q.strip()]
        valores_lista = [v.strip() for v in valores.split(",") if v.strip()]

        quantidades_int = []
        valores_float = []
        for q in quantidades_lista:
            quantidades_int.append(int(q))
        for v in valores_lista:
            valores_float.append(float(v))

        # Usar o valor_total já calculado no salvar_pedido
        valor_total = valor_total_calculado[0]

        try:
            cursor.execute("INSERT INTO pedido (status, valor_total, datahora, idmesa, id_usuario) VALUES ('em andamento', %s, NOW(), %s, %s)", (valor_total, mesa_numero, id_usuario_logado))
            bd.commit()
            pedido_id = cursor.lastrowid

            for item, qtd, val in zip(itens_lista, quantidades_int, valores_float):
                cursor.execute("INSERT INTO item_pedido (id_pedido, item, valor, quantidade) VALUES (%s, %s, %s, %s)", (pedido_id, item, val, qtd))
            bd.commit()

            # Marcar mesa como em uso quando um pedido é adicionado
            cursor.execute("UPDATE mesa SET em_uso = TRUE WHERE numero = %s", (mesa_numero,))
            bd.commit()

            mensagem_popup.configure(text="Pedido criado com sucesso!", text_color="#4CAF50")  
            popup.after(2000, lambda: (popup.destroy(), carregar_mesas(), carregar_status()))  

        except mysql.connector.Error as e:
            mensagem_popup.configure(text=f"Erro ao criar pedido: {str(e)}", text_color="#FF6B6B")
        except Exception as e:
            mensagem_popup.configure(text=f"Erro inesperado: {str(e)}", text_color="#FF6B6B")

    def salvar_pedido():
        if confirmando[0]:
            confirmar_salvamento()
            return

        itens = entrada_itens.get().strip()
        quantidades = entrada_quantidades.get().strip()
        valores = entrada_valores.get().strip()

        if not itens:
            mensagem_popup.configure(text="Campo 'Itens' é obrigatório.", text_color="#FF6B6B")
            return
        if not quantidades:
            mensagem_popup.configure(text="Campo 'Quantidades' é obrigatório.", text_color="#FF6B6B")
            return
        if not valores:
            mensagem_popup.configure(text="Campo 'Valores' é obrigatório.", text_color="#FF6B6B")
            return

        itens_lista = [item.strip() for item in itens.split(",") if item.strip()]
        quantidades_lista = [q.strip() for q in quantidades.split(",") if q.strip()]
        valores_lista = [v.strip() for v in valores.split(",") if v.strip()]

        if len(itens_lista) != len(quantidades_lista) or len(itens_lista) != len(valores_lista):
            mensagem_popup.configure(text="Número de itens, quantidades e valores deve ser igual.", text_color="#FF6B6B")
            return

        if not itens_lista:
            mensagem_popup.configure(text="Nenhum item válido encontrado.", text_color="#FF6B6B")
            return

        try:
            quantidades_int = []
            valores_float = []
            valor_total = 0.0
            for q in quantidades_lista:
                q_int = int(q)
                if q_int <= 0:
                    raise ValueError(f"Quantidade '{q}' deve ser um número positivo.")
                quantidades_int.append(q_int)
            for v in valores_lista:
                v_float = float(v)
                if v_float <= 0:
                    raise ValueError(f"Valor '{v}' deve ser um número positivo.")
                valores_float.append(v_float)

            for q, v in zip(quantidades_int, valores_float):
                valor_total += q * v
            
            # Armazenar o valor total calculado
            valor_total_calculado[0] = valor_total
        except ValueError as e:
            mensagem_popup.configure(text=f"Erro de validação: {str(e)}", text_color="#FF6B6B")
            return

        mensagem_popup.configure(text=f"Confirmar pedido com valor total de R$ {valor_total:.2f}?", text_color="#FFFFFF")
        confirmando[0] = True
        btn_salvar.configure(text="Sim", command=confirmar_salvamento)
        btn_cancelar.configure(text="Não", command=voltar)

    btn_salvar.configure(command=salvar_pedido)
    btn_salvar.pack(side="left", padx=10)
    btn_cancelar.configure(command=popup.destroy)
    btn_cancelar.pack(side="right", padx=10)


    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")

# ================== STATUS E HISTÓRICO ==================
def carregar_status():
    global frame_status
    for widget in frame_status.winfo_children():
        widget.destroy()
    
    scrollable_frame = ctk.CTkScrollableFrame(frame_status, fg_color="#2E2E2E", corner_radius=10)
    scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    titulo = ctk.CTkLabel(scrollable_frame, text="🍽️ Status dos Pedidos", font=("Arial", 24, "bold"), text_color="#FFFFFF", fg_color="#1E1E1E", corner_radius=10)
    titulo.pack(pady=20, fill="x", padx=10)
    
    try:
        cursor.execute("""
            SELECT p.id, p.status, p.valor_total, p.datahora, p.idmesa, ip.item, ip.quantidade, ip.valor
            FROM pedido p 
            JOIN item_pedido ip ON p.id = ip.id_pedido
            WHERE p.status = 'em andamento' AND p.id_usuario = %s
        """, (id_usuario_logado,))
        pedidos = cursor.fetchall()
        
        if not pedidos:
            msg_vazio = ctk.CTkLabel(scrollable_frame, text="Nenhum pedido em andamento. 😊", font=("Arial", 16), text_color="#CCCCCC", fg_color="#1E1E1E", corner_radius=10)
            msg_vazio.pack(pady=10, padx=10, fill="x")
        else:

            pedidos_por_mesa = {}
            for pedido in pedidos:
                id_pedido, status, valor_total, datahora, idmesa, item, quantidade, valor = pedido
                if idmesa not in pedidos_por_mesa:
                    pedidos_por_mesa[idmesa] = {}
                if id_pedido not in pedidos_por_mesa[idmesa]:
                    pedidos_por_mesa[idmesa][id_pedido] = {
                        'valor_total': valor_total,
                        'datahora': datahora,
                        'itens': []
                    }
                pedidos_por_mesa[idmesa][id_pedido]['itens'].append(f"{item} ({quantidade}x R${valor:.2f})")
            
        
            for idmesa, pedidos_mesa in pedidos_por_mesa.items():
                
                frame_mesa = ctk.CTkFrame(scrollable_frame, fg_color="#81A1C1", corner_radius=15)
                frame_mesa.pack(pady=10, fill="x", padx=20)
                
                titulo_mesa = ctk.CTkLabel(frame_mesa, text=f"🍴 Mesa {idmesa}", font=("Arial", 20, "bold"), text_color="#FFFFFF")
                titulo_mesa.pack(pady=10)
                
                
                num_pedidos = len(pedidos_mesa)
                altura_textbox = max(150, 50 * num_pedidos + 100)  
                textbox = ctk.CTkTextbox(frame_mesa, height=altura_textbox, wrap="word", fg_color="#ECEFF4", text_color="#2E3440", font=("Arial", 12), corner_radius=8)
                textbox.pack(pady=5, fill="x", padx=10)
                textbox.configure(state="normal")  
                
                for id_pedido, detalhes in pedidos_mesa.items():
                    itens_str = ", ".join(detalhes['itens'])
                    texto_pedido = f"📋 Pedido {id_pedido}: {itens_str} - Valor Total: R${detalhes['valor_total']:.2f} - Data: {detalhes['datahora']}\n\n"
                    textbox.insert("end", texto_pedido)
                
                textbox.configure(state="disabled") 
                
                for id_pedido in pedidos_mesa.keys():
                    btn_finalizar = ctk.CTkButton(frame_mesa, text=f"✅ Finalizar Pedido {id_pedido}", command=lambda p=id_pedido: finalizar_pedido(p), 
                                                  fg_color="#A3BE8C", hover_color="#B48EAD", font=("Arial", 14, "bold"), width=200, height=40, corner_radius=8)
                    btn_finalizar.pack(pady=5)
    
    except mysql.connector.Error as e:
        erro_label = ctk.CTkLabel(scrollable_frame, text=f"❌ Erro ao carregar status: {e}", font=("Arial", 14), text_color="#FF6B6B", fg_color="#1E1E1E", corner_radius=10)
        erro_label.pack(pady=10, padx=10, fill="x")


def finalizar_pedido(pedido_id):
    popup = ctk.CTkToplevel()
    popup.title("Finalizar Pedido")
    popup.geometry("350x200")
    popup.resizable(False, False)
    popup.transient(janela)
    popup.grab_set()
    popup.configure(fg_color="#2E2E2E")

    titulo = ctk.CTkLabel(popup, text="Finalizar Pedido", font=("Arial", 18, "bold"), text_color="#FFFFFF")
    titulo.pack(pady=20)

    mensagem = ctk.CTkLabel(popup, text=f"Tem certeza de que deseja finalizar o pedido {pedido_id}?", font=("Arial", 14), text_color="#CCCCCC")
    mensagem.pack(pady=10)

    frame_botoes = ctk.CTkFrame(popup, fg_color="transparent")
    frame_botoes.pack(pady=10)

    def confirmar():
        try:
            cursor.execute("UPDATE pedido SET status = 'finalizado' WHERE id = %s", (pedido_id,))
            bd.commit()
            popup.destroy()
            label_temp = ctk.CTkLabel(frame_status, text="✅ Pedido finalizado com sucesso!", font=("Arial", 14), text_color="#A3BE8C", fg_color="#1E1E1E", corner_radius=10)
            label_temp.pack(pady=10)
            frame_status.after(2000, label_temp.destroy)
            carregar_status()
            carregar_historico()
        except mysql.connector.Error as e:
            popup.destroy()
            label_temp = ctk.CTkLabel(frame_status, text=f"❌ Erro ao finalizar pedido: {e}", font=("Arial", 14), text_color="#FF6B6B", fg_color="#1E1E1E", corner_radius=10)
            label_temp.pack(pady=10)
            frame_status.after(3000, label_temp.destroy)

    btn_sim = ctk.CTkButton(frame_botoes, text="Sim", command=confirmar, fg_color="#4CAF50", hover_color="#45A049", width=100, height=40, corner_radius=8)
    btn_nao = ctk.CTkButton(frame_botoes, text="Não", command=popup.destroy, fg_color="#F44336", hover_color="#D32F2F", width=100, height=40, corner_radius=8)
    btn_sim.pack(side="left", padx=10)
    btn_nao.pack(side="right", padx=10)

    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")


def carregar_historico():
    global frame_historico
    for widget in frame_historico.winfo_children():
        widget.destroy()
    
    scrollable_frame = ctk.CTkScrollableFrame(frame_historico, fg_color="#2E2E2E", corner_radius=10)
    scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    titulo = ctk.CTkLabel(scrollable_frame, text="📜 Histórico de Pedidos", font=("Arial", 24, "bold"), text_color="#FFFFFF", fg_color="#1E1E1E", corner_radius=10)
    titulo.pack(pady=20, fill="x", padx=10)
    
    try:
        cursor.execute("""
            SELECT p.id, p.status, p.valor_total, p.datahora, p.idmesa, ip.item, ip.quantidade, ip.valor
            FROM pedido p 
            JOIN item_pedido ip ON p.id = ip.id_pedido
            WHERE p.status = 'finalizado' AND p.id_usuario = %s
        """, (id_usuario_logado,))
        pedidos = cursor.fetchall()
        
        if not pedidos:
            msg_vazio = ctk.CTkLabel(scrollable_frame, text="Nenhum pedido finalizado. 😊", font=("Arial", 16), text_color="#CCCCCC", fg_color="#1E1E1E", corner_radius=10)
            msg_vazio.pack(pady=10, padx=10, fill="x")
        else:
            pedidos_por_mesa = {}
            for pedido in pedidos:
                id_pedido, status, valor_total, datahora, idmesa, item, quantidade, valor = pedido
                if idmesa not in pedidos_por_mesa:
                    pedidos_por_mesa[idmesa] = {}
                if id_pedido not in pedidos_por_mesa[idmesa]:
                    pedidos_por_mesa[idmesa][id_pedido] = {
                        'valor_total': valor_total,
                        'datahora': datahora,
                        'itens': []
                    }
                pedidos_por_mesa[idmesa][id_pedido]['itens'].append(f"{item} ({quantidade}x R${valor:.2f})")
            
            for idmesa, pedidos_mesa in pedidos_por_mesa.items():
                frame_mesa = ctk.CTkFrame(scrollable_frame, fg_color="#81A1C1", corner_radius=15)
                frame_mesa.pack(pady=10, fill="x", padx=20)
                
                titulo_mesa = ctk.CTkLabel(frame_mesa, text=f"🍴 Mesa {idmesa}", font=("Arial", 20, "bold"), text_color="#FFFFFF")
                titulo_mesa.pack(pady=10)
                
                num_pedidos = len(pedidos_mesa)
                altura_textbox = max(150, 50 * num_pedidos + 100)
                textbox = ctk.CTkTextbox(frame_mesa, height=altura_textbox, wrap="word", fg_color="#ECEFF4", text_color="#2E3440", font=("Arial", 12), corner_radius=8)
                textbox.pack(pady=5, fill="x", padx=10)
                textbox.configure(state="normal")
                
                for id_pedido, detalhes in pedidos_mesa.items():
                    itens_str = ", ".join(detalhes['itens'])
                    texto_pedido = f"📋 Pedido {id_pedido}: {itens_str} - Valor Total: R${detalhes['valor_total']:.2f} - Data: {detalhes['datahora']}\n\n"
                    textbox.insert("end", texto_pedido)
                
                textbox.configure(state="disabled")
    
    except mysql.connector.Error as e:
        erro_label = ctk.CTkLabel(scrollable_frame, text=f"❌ Erro ao carregar histórico: {e}", font=("Arial", 14), text_color="#FF6B6B", fg_color="#1E1E1E", corner_radius=10)
        erro_label.pack(pady=10, padx=10, fill="x")


# ================== TELAS PRINCIPAIS ==================
telabemvindo = ctk.CTkFrame(janela)
telacadastro = ctk.CTkFrame(janela)
telalogin = ctk.CTkFrame(janela)
telaprincipal = ctk.CTkFrame(janela)

for tela in (telabemvindo, telacadastro, telalogin, telaprincipal):
    tela.grid(row=0, column=0, sticky="nsew")

# --- Tela Bem-vindo ---
ctk.CTkLabel(telabemvindo, text="").pack(pady=60)
img = ctk.CTkImage(light_image=Image.open("sla.png"), size=(300, 110))
ctk.CTkLabel(telabemvindo, image=img, text="").pack(pady=50)
ctk.CTkButton(telabemvindo, text="Cadastro", font=("Arial", 25, "bold"), width=250, height=55, command=lambda: mostrartela(telacadastro)).pack(pady=15)
ctk.CTkButton(telabemvindo, text="Login", font=("Arial", 25, "bold"), width=250, height=55, command=lambda: mostrartela(telalogin)).pack(pady=10)

# --- Tela Cadastro ---
ctk.CTkLabel(telacadastro, text="").pack(pady=5)
ctk.CTkLabel(telacadastro, text="Cadastro de Funcionário",  font=("Arial", 50, "bold")).pack(pady=40)
entrada_nome = ctk.CTkEntry(telacadastro, placeholder_text="Nome completo", font=("Arial", 30), width=550, height=50)
entrada_nome.pack(pady=15)
entrada_cpf = ctk.CTkEntry(telacadastro, placeholder_text="CPF", font=("Arial", 30), width=550, height=50)
entrada_cpf.pack(pady=15)
entrada_senha = ctk.CTkEntry(telacadastro, placeholder_text="Senha (6 dígitos)", show="*", font=("Arial", 30), width=550, height=50)
entrada_senha.pack(pady=15)
mensagem_cadastro = ctk.CTkLabel(telacadastro, text="", font=("Arial", 20))
mensagem_cadastro.pack(pady=10)
ctk.CTkButton(telacadastro, text="Cadastrar", font=("Arial", 25, "bold"), width=220, height=50, command=cadastrar).pack(pady=10)
ctk.CTkButton(telacadastro, text="Voltar ao Menu",  font=("Arial", 25, "bold"), width=220, height=50, command=lambda: mostrartela(telabemvindo)).pack(pady=20)

# --- Tela Login ---
ctk.CTkLabel(telalogin, text="").pack(pady=5)
ctk.CTkLabel(telalogin, text="Login", font=("Arial", 50, "bold")).pack(pady=40)
entrada_login_cpf = ctk.CTkEntry(telalogin, placeholder_text="CPF", font=("Arial", 30), width=550, height=50)
entrada_login_cpf.pack(pady=15)
entrada_login_senha = ctk.CTkEntry(telalogin, placeholder_text="Senha", show="*",font=("Arial", 30), width=550, height=50)
entrada_login_senha.pack(pady=15)
mensagem_login = ctk.CTkLabel(telalogin, text="", font=("Arial", 20))
mensagem_login.pack(pady=10)
ctk.CTkButton(telalogin, text="Entrar",  font=("Arial", 25, "bold"), width=220, height=50, command=logar).pack(pady=10)
ctk.CTkButton(telalogin, text="Voltar ao Menu",  font=("Arial", 25, "bold"), width=220, height=50, command=lambda: mostrartela(telabemvindo)).pack(pady=20)


def mostrar_subtela(subtela):
    subtela.tkraise()

# --- Tela Principal ---
def configurar_tela_principal(janela, telaprincipal, telabemvindo):
    # Destruir todos os widgets existentes em telaprincipal para evitar telas repetidas
    for widget in telaprincipal.winfo_children():
        widget.destroy()
    
    global frame_mesas, frame_status, frame_historico

    titulo = ctk.CTkLabel(telaprincipal, text="Painel de Pedidos", font=("Arial", 20, "bold"))
    titulo.pack(side="top", anchor="w", padx=10, pady=20)
    
    barra_lateral = ctk.CTkFrame(telaprincipal, width=250, corner_radius=10)
    barra_lateral.pack(side="left", fill="y", padx=10, pady=10)
    
    area_principal = ctk.CTkFrame(telaprincipal, corner_radius=10)
    area_principal.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    area_principal.grid_columnconfigure(0, weight=1)
    area_principal.grid_rowconfigure(0, weight=1)
    
    frame_mesas = ctk.CTkFrame(area_principal)
    frame_status = ctk.CTkFrame(area_principal)
    frame_historico = ctk.CTkFrame(area_principal)
    for subframe in (frame_mesas, frame_status, frame_historico):
        subframe.grid(row=0, column=0, sticky="nsew")

    carregar_mesas()
    carregar_status()
    carregar_historico()

    
    btn_mesas = ctk.CTkButton(barra_lateral, text="🍽️Mesas", font=("Arial", 14), command=lambda: mostrar_subtela(frame_mesas))
    btn_mesas.pack(pady=15, padx=10, fill="x")
    btn_status = ctk.CTkButton(barra_lateral, text="📊 Status", font=("Arial", 14), command=lambda: mostrar_subtela(frame_status))
    btn_status.pack(pady=15, padx=10, fill="x")
    btn_historico = ctk.CTkButton(barra_lateral, text="📜 Histórico", font=("Arial", 14), command=lambda: mostrar_subtela(frame_historico))
    btn_historico.pack(pady=15, padx=10, fill="x")
    
    separador = ctk.CTkFrame(barra_lateral, height=2)
    separador.pack(fill="x", pady=10)
    btn_logout = ctk.CTkButton(barra_lateral, text="🚪 Logout", font=("Arial", 14), fg_color="orange", command=logout)
    btn_logout.pack(pady=10, padx=10, fill="x")
    btn_sair = ctk.CTkButton(barra_lateral, text="❌ Sair do App", font=("Arial", 14), fg_color="red", command=janela.quit)
    btn_sair.pack(pady=10, padx=10, fill="x")
    mostrar_subtela(frame_mesas)


mostrartela(telabemvindo)
janela.mainloop()