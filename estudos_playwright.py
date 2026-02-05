from playwright.sync_api import sync_playwright
import time
# abrir um navegador

#cria uma "instacia" do navegador, "pw" gerencia o navegador
with sync_playwright() as pw:
    navegador = pw.chromium.launch(headless= False) # abre o navegador
    # por padrao, o playwright abre o navegador em segundo plano (headless = True). Se quiser ver o navegador aberto, passar o paramento headless = False dentro do launch 

    pagina = navegador.new_page() # cria a nova pagina, variavel na qual vamos mexer

    # navegar para uma pagina
    pagina.goto("https://www.hashtagtreinamentos.com/") # sempre pasando http/https

   

    # pegar infos da pagina

    print(pagina.title()) # .title() retorna o titulo da pagina

    # selecionar elementos na tela (existem varias formas)
   #por xpath, por role etc

   


    time.sleep(5)

    navegador.close() # fecha o navegador