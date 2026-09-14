"use strict";

/*
============================================================
 J.A.R.V.I.S — INTERFACE NEURAL
============================================================
*/


// ============================================================
// CONFIGURAÇÃO
// ============================================================

const API_URL = "";

const STATUS_INTERVAL = 1000;


// ============================================================
// ELEMENTOS
// ============================================================

const neuralCanvas = document.getElementById("neuralCanvas");
const neuralCore = document.getElementById("neuralCore");

const commandInput = document.getElementById("commandInput");
const sendButton = document.getElementById("sendButton");
const voiceButton = document.getElementById("voiceButton");

const connectionDot = document.getElementById("connectionDot");
const connectionStatus = document.getElementById("connectionStatus");

const coreState = document.getElementById("coreState");
const coreDescription = document.getElementById("coreDescription");

const activityProgress = document.getElementById("activityProgress");

const chat = document.getElementById("chat");
const activityLog = document.getElementById("activityLog");

const cpuValue = document.getElementById("cpuValue");
const ramValue = document.getElementById("ramValue");
const gpuValue = document.getElementById("gpuValue");

const cpuBar = document.getElementById("cpuBar");
const ramBar = document.getElementById("ramBar");
const gpuBar = document.getElementById("gpuBar");

const apiStatus = document.getElementById("apiStatus");
const iaStatus = document.getElementById("iaStatus");
const voiceStatus = document.getElementById("voiceStatus");
const visionStatus = document.getElementById("visionStatus");
const memoryStatus = document.getElementById("memoryStatus");

const uptime = document.getElementById("uptime");

const inputStatus = document.getElementById("inputStatus");


// ============================================================
// ESTADO
// ============================================================

let currentState = "idle";
let lastStatus = null;
let commandInProgress = false;

let lastActivityMessage = "";
let lastActivityTime = 0;


// ============================================================
// SEGURANÇA
// ============================================================

function safeElement(element, callback) {

    if (!element) {
        return;
    }

    callback(element);

}


// ============================================================
// HORA
// ============================================================

function getTime() {

    return new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });

}


// ============================================================
// LOG DE ATIVIDADE
// ============================================================

function addActivity(message, force = false) {

    if (!activityLog) {
        return;
    }

    const now = Date.now();

    /*
    Evita que o polling de status fique adicionando
    "Aguardando comando" infinitamente.
    */

    if (
        !force &&
        message === lastActivityMessage &&
        now - lastActivityTime < 1500
    ) {
        return;
    }

    lastActivityMessage = message;
    lastActivityTime = now;


    const line = document.createElement("div");

    /*
    Compatibilidade com os dois estilos de CSS.
    */

    line.className = "activity-line log-entry";


    line.innerHTML = `
        <span class="activity-time">
            ${getTime()}
        </span>

        <span>
            ${escapeHtml(message)}
        </span>
    `;


    activityLog.prepend(line);


    while (activityLog.children.length > 30) {

        activityLog.removeChild(
            activityLog.lastChild
        );

    }

}


// ============================================================
// CHAT
// ============================================================

function addChatMessage(author, message, type = "jarvis") {

    if (!chat) {
        return;
    }


    const wrapper =
        document.createElement("div");


    wrapper.className =
        `chat-message ${type}`;


    wrapper.innerHTML = `
        <div class="chat-author chat-label">
            ${escapeHtml(author)}
        </div>

        <div class="chat-text">
            ${escapeHtml(message)}
        </div>
    `;


    chat.appendChild(wrapper);


    chat.scrollTop =
        chat.scrollHeight;

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


// ============================================================
// ESTADO DO NÚCLEO
// ============================================================

function setState(state, description = "", writeLog = true) {

    state =
        String(state || "idle")
            .toLowerCase();


    currentState = state;


    const states = {

        idle: {
            label: "STANDBY",
            description: "Aguardando comando",
            progress: 0
        },

        standby: {
            label: "STANDBY",
            description: "Aguardando comando",
            progress: 0
        },

        ready: {
            label: "STANDBY",
            description: "Sistema pronto",
            progress: 0
        },

        listening: {
            label: "OUVINDO",
            description: "Aguardando sua voz...",
            progress: 20
        },

        attention: {
            label: "ATENÇÃO",
            description: "Atenção ativada.",
            progress: 30
        },

        processing: {
            label: "PROCESSANDO",
            description: "Analisando comando...",
            progress: 45
        },

        thinking: {
            label: "PENSANDO",
            description: "Processando informação...",
            progress: 65
        },

        working: {
            label: "EXECUTANDO",
            description: "Executando tarefa...",
            progress: 80
        },

        executing: {
            label: "EXECUTANDO",
            description: "Executando tarefa...",
            progress: 85
        },

        speaking: {
            label: "RESPONDENDO",
            description: "Preparando resposta...",
            progress: 70
        },

        error: {
            label: "ERRO",
            description: "Falha durante processamento",
            progress: 0
        }

    };


    const info =
        states[state] ||
        states.idle;


    safeElement(
        neuralCore,
        element => {

            element.className =
                "neural-core " + state;

        }
    );


    safeElement(
        coreState,
        element => {

            element.textContent =
                info.label;

        }
    );


    safeElement(
        coreDescription,
        element => {

            element.textContent =
                description ||
                info.description;

        }
    );


    safeElement(
        activityProgress,
        element => {

            element.style.width =
                `${info.progress}%`;

        }
    );


    if (writeLog) {

        addActivity(
            description ||
            info.description
        );

    }

}


// ============================================================
// CONEXÃO
// ============================================================

function updateConnection(online) {

    safeElement(
        connectionDot,
        element => {

            element.classList.toggle(
                "online",
                online
            );

            element.classList.toggle(
                "offline",
                !online
            );

        }
    );


    safeElement(
        connectionStatus,
        element => {

            element.textContent =
                online
                    ? "ONLINE"
                    : "OFFLINE";

        }
    );

}


// ============================================================
// TELEMETRIA
// ============================================================

function updateTelemetry(data) {

    const cpu =
        Number(
            data?.cpu ??
            data?.cpu_percent ??
            0
        );


    const ram =
        Number(
            data?.ram ??
            data?.ram_percent ??
            0
        );


    const gpuAvailable =
        data?.gpu != null ||
        data?.gpu_percent != null;


    const gpu =
        Number(
            data?.gpu ??
            data?.gpu_percent ??
            0
        );


    safeElement(
        cpuValue,
        element => {

            element.textContent =
                `${Math.round(cpu)}%`;

        }
    );


    safeElement(
        ramValue,
        element => {

            element.textContent =
                `${Math.round(ram)}%`;

        }
    );


    safeElement(
        gpuValue,
        element => {

            element.textContent =
                gpuAvailable
                    ? `${Math.round(gpu)}%`
                    : "--%";

        }
    );


    safeElement(
        cpuBar,
        element => {

            element.style.width =
                `${clamp(cpu)}%`;

        }
    );


    safeElement(
        ramBar,
        element => {

            element.style.width =
                `${clamp(ram)}%`;

        }
    );


    safeElement(
        gpuBar,
        element => {

            element.style.width =
                `${clamp(gpu)}%`;

        }
    );

}


function clamp(value) {

    return Math.min(
        100,
        Math.max(
            0,
            Number(value) || 0
        )
    );

}


// ============================================================
// STATUS DO BACKEND
// ============================================================

function normalizeStatus(status) {

    status =
        String(status || "ready")
            .toLowerCase()
            .trim();


    const map = {

        ready: "idle",

        standby: "idle",

        idle: "idle",

        aguardando: "idle",

        ouvindo: "listening",

        listening: "listening",

        attention: "attention",

        atenção: "attention",

        processing: "processing",

        processando: "processing",

        thinking: "thinking",

        pensando: "thinking",

        working: "working",

        executando: "executing",

        executing: "executing",

        speaking: "speaking",

        respondendo: "speaking",

        error: "error",

        erro: "error"

    };


    return map[status] || "idle";

}


// ============================================================
// ATUALIZAÇÃO DA INTERFACE
// ============================================================

function updateInterface(data) {

    if (!data) {
        return;
    }


    lastStatus = data;


    updateConnection(true);


    const backendStatus =
        normalizeStatus(
            data.status
        );


    /*
    Não deixa o polling destruir o estado visual
    enquanto existe um comando sendo executado.
    */

    if (commandInProgress) {

        if (
            backendStatus !== "idle" &&
            backendStatus !== "ready"
        ) {

            setState(
                backendStatus,
                data.descricao ||
                data.description ||
                undefined,
                false
            );

        }

    }

    else {

        setState(
            backendStatus,
            data.descricao ||
            data.description ||
            undefined,
            false
        );

    }


    // --------------------------------------------------------
    // SISTEMA
    // --------------------------------------------------------

    safeElement(
        apiStatus,
        element => {

            element.textContent =
                "ONLINE";

        }
    );


    safeElement(
        iaStatus,
        element => {

            element.textContent =
                data.ia ??
                data.ia_status ??
                data.IA ??
                "ONLINE";

        }
    );


    safeElement(
        voiceStatus,
        element => {

            element.textContent =
                data.voz ??
                data.voice ??
                data.voice_status ??
                "---";

        }
    );


    safeElement(
        visionStatus,
        element => {

            element.textContent =
                data.visao ??
                data.vision ??
                data.vision_status ??
                "---";

        }
    );


    safeElement(
        memoryStatus,
        element => {

            element.textContent =
                data.memoria ??
                data.memory ??
                data.memory_status ??
                "ATIVA";

        }
    );


    updateTelemetry(data);


    if (data.inicio != null) {

        updateUptime(
            data.inicio
        );

    }

}


// ============================================================
// UPTIME
// ============================================================

function updateUptime(startTime) {

    if (!uptime) {
        return;
    }


    const start =
        Number(startTime);


    if (!start) {
        return;
    }


    /*
    Aceita timestamp em segundos ou milissegundos.
    */

    const startSeconds =
        start > 100000000000
            ? start / 1000
            : start;


    const now =
        Date.now() / 1000;


    const seconds =
        Math.max(
            0,
            Math.floor(
                now - startSeconds
            )
        );


    const h =
        String(
            Math.floor(
                seconds / 3600
            )
        ).padStart(2, "0");


    const m =
        String(
            Math.floor(
                (seconds % 3600) / 60
            )
        ).padStart(2, "0");


    const s =
        String(
            seconds % 60
        ).padStart(2, "0");


    uptime.textContent =
        `${h}:${m}:${s}`;

}


// ============================================================
// GET STATUS
// ============================================================

async function getStatus() {

    try {

        const response =
            await fetch(
                `${API_URL}/api/status`,
                {
                    method: "GET",
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        updateInterface(data);

    }

    catch (error) {

        updateConnection(false);


        safeElement(
            apiStatus,
            element => {

                element.textContent =
                    "OFFLINE";

            }
        );


        /*
        Não polui o log a cada segundo.
        */

        addActivity(
            `API offline: ${error.message}`
        );

    }

}


// ============================================================
// EXTRAI RESPOSTA
// ============================================================

function extractResponse(data) {

    if (!data) {
        return "Comando processado.";
    }


    const candidates = [

        data.resposta,

        data.response,

        data.message,

        data.mensagem,

        data.resultado,

        data.result,

        data.output,

        data.text,

        data.reply

    ];


    for (const value of candidates) {

        if (
            value !== undefined &&
            value !== null &&
            String(value).trim()
        ) {

            return String(value);

        }

    }


    return "Comando processado.";

}


// ============================================================
// ENVIO DO COMANDO
// ============================================================

async function sendCommand(command) {

    command =
        String(command ?? "").trim();


    if (!command) {

        safeElement(
            commandInput,
            element => element.focus()
        );

        return;

    }


    if (commandInProgress) {

        addActivity(
            "J.A.R.V.I.S ocupado. Aguarde a execução terminar.",
            true
        );

        return;

    }


    commandInProgress = true;


    // --------------------------------------------------------
    // INTERFACE
    // --------------------------------------------------------

    addChatMessage(
        "VOCÊ",
        command,
        "user"
    );


    addActivity(
        `Comando recebido: ${command}`,
        true
    );


    setState(
        "processing",
        "Analisando comando..."
    );


    safeElement(
        sendButton,
        element => {

            element.disabled = true;

            element.style.opacity =
                "0.45";

            element.style.cursor =
                "wait";

        }
    );


    safeElement(
        commandInput,
        element => {

            element.value = "";

            element.disabled = true;

        }
    );


    safeElement(
        inputStatus,
        element => {

            element.textContent =
                "PROCESSANDO...";

        }
    );


    try {

        const response =
            await fetch(
                `${API_URL}/api/comando`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body: JSON.stringify({
                        comando: command
                    })
                }
            );


        const text =
            await response.text();


        let data;


        try {

            data =
                text
                    ? JSON.parse(text)
                    : {};

        }

        catch {

            data = {
                resposta: text
            };

        }


        if (!response.ok) {

            throw new Error(
                data?.erro ??
                data?.error ??
                data?.message ??
                data?.mensagem ??
                data?.resposta ??
                `HTTP ${response.status}`
            );

        }


        // ----------------------------------------------------
        // RESPOSTA
        // ----------------------------------------------------

        const resposta =
            extractResponse(data);


        setState(
            "speaking",
            "Resposta recebida."
        );


        addChatMessage(
            "J.A.R.V.I.S",
            resposta,
            "jarvis"
        );


        addActivity(
            "Comando concluído.",
            true
        );


    }

    catch (error) {

        console.error(
            "Erro ao enviar comando:",
            error
        );


        setState(
            "error",
            "Falha ao executar comando."
        );


        addChatMessage(
            "J.A.R.V.I.S",
            `Erro: ${error.message}`,
            "jarvis"
        );


        addActivity(
            `ERRO: ${error.message}`,
            true
        );

    }

    finally {

        commandInProgress = false;


        safeElement(
            sendButton,
            element => {

                element.disabled =
                    false;

                element.style.opacity =
                    "1";

                element.style.cursor =
                    "pointer";

            }
        );


        safeElement(
            commandInput,
            element => {

                element.disabled =
                    false;

                element.focus();

            }
        );


        safeElement(
            inputStatus,
            element => {

                element.textContent =
                    "ENTER PARA ENVIAR";

            }
        );


        /*
        Pequeno intervalo para mostrar o estado
        RESPONDENDO antes de voltar ao standby.
        */

        setTimeout(
            () => {

                if (!commandInProgress) {

                    setState(
                        "idle",
                        "Aguardando comando"
                    );

                }

            },
            900
        );

    }

}


// ============================================================
// TECLADO
// ============================================================

function handleCommandKey(event) {

    if (
        event.key !== "Enter" ||
        event.isComposing
    ) {

        return;

    }


    /*
    SHIFT + ENTER
    = nova linha
    */

    if (event.shiftKey) {
        return;
    }


    event.preventDefault();


    if (!commandInProgress) {

        sendCommand(
            commandInput?.value
        );

    }

}


// ============================================================
// AUTO RESIZE DO TEXTAREA
// ============================================================

function autoResizeInput() {

    if (!commandInput) {
        return;
    }


    commandInput.style.height =
        "auto";


    const height =
        Math.min(
            Math.max(
                commandInput.scrollHeight,
                58
            ),
            150
        );


    commandInput.style.height =
        `${height}px`;

}


// ============================================================
// CANVAS NEURAL
// ============================================================

function setupNeuralCanvas() {

    if (!neuralCanvas) {
        return;
    }


    const canvas =
        neuralCanvas;


    const ctx =
        canvas.getContext("2d");


    if (!ctx) {
        return;
    }


    let width = 0;
    let height = 0;


    function resize() {

        const rect =
            canvas.getBoundingClientRect();


        const dpr =
            Math.min(
                window.devicePixelRatio || 1,
                2
            );


        width =
            Math.max(
                1,
                Math.floor(
                    rect.width * dpr
                )
            );


        height =
            Math.max(
                1,
                Math.floor(
                    rect.height * dpr
                )
            );


        canvas.width =
            width;


        canvas.height =
            height;


        canvas.style.width =
            `${rect.width}px`;


        canvas.style.height =
            `${rect.height}px`;


        ctx.setTransform(
            dpr,
            0,
            0,
            dpr,
            0,
            0
        );

    }


    window.addEventListener(
        "resize",
        resize
    );


    resize();


    const particles = [];


    const PARTICLE_COUNT = 85;


    function createParticle() {

        const angle =
            Math.random() *
            Math.PI *
            2;


        const radius =
            Math.sqrt(
                Math.random()
            );


        return {

            x:
                0.5 +
                Math.cos(angle) *
                radius *
                0.48,

            y:
                0.5 +
                Math.sin(angle) *
                radius *
                0.48,

            vx:
                (Math.random() - 0.5) *
                0.0009,

            vy:
                (Math.random() - 0.5) *
                0.0009,

            radius:
                Math.random() * 1.5 +
                0.5

        };

    }


    for (
        let i = 0;
        i < PARTICLE_COUNT;
        i++
    ) {

        particles.push(
            createParticle()
        );

    }


    function animate() {

        const rect =
            canvas.getBoundingClientRect();


        const w =
            rect.width;


        const h =
            rect.height;


        ctx.clearRect(
            0,
            0,
            w,
            h
        );


        const active =
            ![
                "idle",
                "standby"
            ].includes(
                currentState
            );


        const energy =
            active
                ? 1
                : 0.35;


        // ----------------------------------------------------
        // PARTÍCULAS
        // ----------------------------------------------------

        for (const particle of particles) {

            if (active) {

                particle.x +=
                    particle.vx *
                    3;

                particle.y +=
                    particle.vy *
                    3;

            }


            /*
            Mantém as partículas dentro do campo.
            */

            if (
                particle.x < 0.02 ||
                particle.x > 0.98
            ) {

                particle.vx *= -1;

            }


            if (
                particle.y < 0.02 ||
                particle.y > 0.98
            ) {

                particle.vy *= -1;

            }


            const x =
                particle.x * w;


            const y =
                particle.y * h;


            ctx.beginPath();


            ctx.arc(
                x,
                y,
                particle.radius,
                0,
                Math.PI * 2
            );


            ctx.fillStyle =
                `rgba(80,210,255,${0.25 + energy * 0.6})`;


            ctx.fill();

        }


        // ----------------------------------------------------
        // CONEXÕES NEURAIS
        // ----------------------------------------------------

        if (active) {

            const maxDistance =
                125;


            for (
                let i = 0;
                i < particles.length;
                i++
            ) {

                for (
                    let j = i + 1;
                    j < particles.length;
                    j++
                ) {

                    const a =
                        particles[i];


                    const b =
                        particles[j];


                    const ax =
                        a.x * w;


                    const ay =
                        a.y * h;


                    const bx =
                        b.x * w;


                    const by =
                        b.y * h;


                    const dx =
                        ax - bx;


                    const dy =
                        ay - by;


                    const distance =
                        Math.sqrt(
                            dx * dx +
                            dy * dy
                        );


                    if (
                        distance <
                        maxDistance
                    ) {

                        const opacity =
                            (
                                1 -
                                distance /
                                maxDistance
                            ) * 0.25;


                        ctx.beginPath();


                        ctx.moveTo(
                            ax,
                            ay
                        );


                        ctx.lineTo(
                            bx,
                            by
                        );


                        ctx.strokeStyle =
                            `rgba(50,190,255,${opacity})`;


                        ctx.lineWidth =
                            1;


                        ctx.stroke();

                    }

                }

            }

        }


        requestAnimationFrame(
            animate
        );

    }


    animate();

}


// ============================================================
// BOTÕES RÁPIDOS
// ============================================================

function setupQuickButtons() {

    const buttons =
        document.querySelectorAll(
            ".quick-button"
        );


    buttons.forEach(
        button => {

            button.addEventListener(
                "click",
                () => {

                    const command =
                        button.dataset.command;


                    if (command) {

                        sendCommand(
                            command
                        );

                    }

                }
            );

        }
    );

}


// ============================================================
// VOZ
// ============================================================

function setupVoiceButton() {

    if (!voiceButton) {
        return;
    }


    voiceButton.addEventListener(
        "click",
        () => {

            /*
            A interface já fica preparada para o módulo
            de voz do JARVIS.

            Não inventamos uma API de voz aqui.
            Quando o backend expuser o endpoint,
            conectamos neste botão.
            */

            addActivity(
                "Comando de voz solicitado.",
                true
            );

        }
    );

}


// ============================================================
// INICIALIZAÇÃO
// ============================================================

function initialize() {

    console.log(
        "J.A.R.V.I.S interface inicializando..."
    );


    addActivity(
        "Conectando ao JARVIS CORE",
        true
    );


    addActivity(
        "Interface neural inicializada",
        true
    );


    // --------------------------------------------------------
    // BOTÃO
    // --------------------------------------------------------

    if (sendButton) {

        sendButton.addEventListener(
            "click",
            () => {

                sendCommand(
                    commandInput?.value
                );

            }
        );

    }


    // --------------------------------------------------------
    // TECLADO
    // --------------------------------------------------------

    if (commandInput) {

        commandInput.addEventListener(
            "keydown",
            handleCommandKey
        );


        commandInput.addEventListener(
            "input",
            autoResizeInput
        );


        commandInput.focus();

        autoResizeInput();

    }


    // --------------------------------------------------------
    // MÓDULOS
    // --------------------------------------------------------

    setupQuickButtons();

    setupVoiceButton();

    setupNeuralCanvas();


    // --------------------------------------------------------
    // API
    // --------------------------------------------------------

    getStatus();


    setInterval(
        getStatus,
        STATUS_INTERVAL
    );


    setInterval(
        () => {

            if (
                lastStatus &&
                lastStatus.inicio
            ) {

                updateUptime(
                    lastStatus.inicio
                );

            }

        },
        1000
    );


    // --------------------------------------------------------
    // ESTADO INICIAL
    // --------------------------------------------------------

    setState(
        "idle",
        "Aguardando comando",
        true
    );

}


document.addEventListener(
    "DOMContentLoaded",
    initialize
);