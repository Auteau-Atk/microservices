/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

const PROCESSING_STATS_API_URL = "processing:8100/stats"
const ANALYZER_API_URL = "analyzer:8110/stats"

// This function fetches and updates the general statistics
const makeReq = (url, cb) => {
    fetch(url)
        .then(res => res.json())
        .then((result) => {
            console.log("Received data: ", result)
            cb(result);
        }).catch((error) => {
            updateErrorMessages(error.message)
        })
}

const updateCodeDiv = (result, elemId) => {
    const elem = document.getElementById(elemId);
    elem.innerHTML = ""; // Clear existing content

    for (const [key, value] of Object.entries(result)) {
        const p = document.createElement("p");
        p.innerHTML = `<strong>${key}:</strong> ${value}`;
        elem.appendChild(p);
    }
};


const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr();
    
    makeReq(PROCESSING_STATS_API_URL, (result) => {
        updateCodeDiv(result, "processing-stats");
        document.getElementById("last-updated-value").innerText = result.latest_timestamp || getLocaleDateStr();
    });

    makeReq(ANALYZER_API_URL, (result) => updateCodeDiv(result, "analyzer-stats"));
};


const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds
}

document.addEventListener('DOMContentLoaded', setup)