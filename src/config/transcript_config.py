from ast import Name


async def createHeader(nameOfTranscript: str):
    header = """
        <head> 
            <meta charset="UTF-8"> 
            <meta name="viewport" 
            content="width=device-width, 
            initial-scale=1.0"> 
            <title>Transcript of """ + nameOfTranscript + """</title> 
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300&display=swap');

            :root {
                --dark-bg: #36393f;
                --dark-server-list: #202225;
                --server-divider: #2d2f32;
                --blurple: #7289da;
                --dark-blurple: #4d5e94;
                --green: #43b581;
                --dark-primary: #2f3136;
                --text-gray: #dcddde;
                --user-box: #292B2F;
                --iconColor: #b9bbbe;
                --red: #dd4444;
            }

            body {
                margin: 0;
                padding: 0;
                background-color: var(--dark-bg);
                color: #FFFFFF;
                font-family: 'Roboto', sans-serif;
            }
            </style>
            <script src="script.js" defer></script> 
        </head>
    """
    return header