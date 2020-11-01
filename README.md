# Cisco Umbrella Investigate & Reporting Webex Teams Bot

Este repositório contém um script em Python que cria um Bot no Webex Teams integrado ao Cisco Umbrella Investigate & Reporting. Para executar este script, você precisa de uma <a href= "https://developer.webex.com/login">conta de desenvolvedor do Webex</a> e seguir <a href = "https://developer.webex.com/docs/bots">esta documentação</a> para criar um bot.

Este script usará uma sala no Webex Teams para registrar todas as mensagens enviadas e recebidas seu Bot. Portanto, você precisará criar uma sala no Webex Teams e incluir seu Bot nela. Use esta <a href = "https://developer.webex.com/docs/api/v1/rooms/list-rooms"> chamada de API</a> para encontrar o roomId.

Um token de acesso <a href="https://docs.umbrella.com/investigate-api/docs/about-the-api-authentication">Cisco Umbrella Investigate API</a> também é necessário para execução do script.

Como o Webex Teams é uma solução em nuvem, por segurança, no arquivo de configuração edite os domínios de emails autorizados para enviar mensagem ao Bot! 
<b> ex: cisco.com, vitait.com</b>

O Bot tem controle de acesso embutido. Certifique-se de modificar a variável webex-domain para obter acesso.

Certifique-se de adicionar seu WebHook usando https://developer.webex.com/docs/api/v1/webhooks/create-a-webhook. Caso queira fazer um com um servidor local, recomendo que use o <a href = "https://ngrok.com/"> Ngrok </a>, uma ferramenta execente para fazer "forwarding" de portas em serviços HTTP.</a> <br>
Exemplo de uso: Pege a URL que está fazendo "forwarding" no Ngrok e coloque no <b>targetUrl</b>, na criação do WebHook do Webex Teams.
<img src="screenshots/ngrok.png"><br><br><br>
  
Se você não tiver as bibliotecas Python necessárias configuradas, receberá um erro ao executar o script. Você precisará instalar o arquivo "requirements.txt": (certifique-se de que está no mesmo diretório que os arquivos clonados do git):<br>
<b> pip install -r requirements.txt</b>

Este repositório contém um ícone de guarda-chuva para o seu bot, umbrella.png
