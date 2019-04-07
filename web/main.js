"use strict";

let lastURL = new URL(window.location);
let thumbnailers = null;


function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function loadTemplate(url) {
    console.log(url);
    let text = await (await fetch(url)).text();
    let el = document.createElement("template");
    el.innerHTML = text.trim();
    return el;
}

function parseInfoFromTitle(title) {
    const match = title.match(
      /^([^\d,.]*)([,.]\s*семинар)?\s*(\d+)\.(.*)$/i
    );

    if (match === null)
        return null;

    const [_, subject, sem, number, rawTopic] = match.map(s => s && s.trim());

    const topic = rawTopic.split(".").map(s => s.trim()).map(
        line => {
            const sublines = [""];
            line.split(" ").forEach(word => {
                if (sublines[sublines.length - 1].length + word.length > 30)
                    sublines.push("");
                sublines[sublines.length - 1] += word + " ";
            });
            return sublines.map(s => s.trim());
        }
    ).flat().filter(s => s.length > 0).join("\n");

    return {subject, number, topic};
}

async function saveExports() {
    let exportsDict = _.fromPairs(thumbnailers.map(app =>
        [app.videoId, {
            subject: app.subject,
            topic: app.topic,
            number: app.number,
            template: app.template,
            fontSize: app.fontSize,
        }]
    ));

    // console.log("Saving exports...");

    await fetch("http://localhost:8888/exports/set", {
        method: "POST",
        /* TODO: learn how to handle preflight cors requests
        headers: {
            "Content-Type": "application/json"
        },
        */
        body: JSON.stringify(exportsDict),
    });

    // console.log("Saved!");
}

let saveExportsThrottled = _.throttle(saveExports, 1000);


// Because template is loaded separetely (webpack/other things are out of my sight)
async function createThumbnailerComponent() {
    return Vue.component("thumbnail-editor", {
        template: await loadTemplate(browser.runtime.getURL("template.html")),
        props: {
            avaliableTemplates: {default: [], required: true},
            videoElement: {required: true},
            videoId:  {required: true},
            subject:  {default: ""},
            topic:    {default: ""},
            number:   {default: ""},
            template: {default: null},
            fontSize: {default: 70},
        },
        data: function() {
            return {
                thumbnailURL: null, // will be set by `created()`
                loading: false,
            }
        },
        created: function () {
            this.reloadThumbnailDebounced = _.debounce(this.reloadThumbnail, 500);
            this.reloadThumbnail();
        },
        watch: {
            subject:  function () { saveExportsThrottled(); },
            template: function () { saveExportsThrottled(); this.reloadThumbnail(); },
            fontSize: function () { saveExportsThrottled(); this.reloadThumbnail(); },
            number:   function () { saveExportsThrottled(); this.reloadThumbnailDebounced(); },
            topic:    function () { saveExportsThrottled(); this.reloadThumbnailDebounced(); },
            thumbnailURL: function() { this.loading = true; },
        },
        computed: {
            sortedAvaliableTemplates: function() {
                const mySynonyms = {
                    "ТПМС": ["Concurrency"],
                }[this.subject] || [this.subject];

                function isGoodTemplate({subject}) {
                    return mySynonyms.some(name =>
                            subject.toLowerCase().includes(name.toLowerCase())
                           )
                }

                return [...this.avaliableTemplates.filter(isGoodTemplate),
                        ...this.avaliableTemplates.filter((templ) => !isGoodTemplate(templ))];
            },
            spinnerURL: () => (browser.runtime.getURL("spinner.gif"))
        },
        methods: {
            genThumbnailURL: function() {
                if (this.template === null)
                    return "https://placehold.it/1920x1080";
                return "http://localhost:8888/thumbnail/preview?" + (new URLSearchParams({
                    number: this.number,
                    topic: this.topic,
                    template: this.template,
                    fontSize: this.fontSize,
                    videoId: this.videoId
                })).toString()
            },
            reloadThumbnail: async function () {
                this.thumbnailURL = this.genThumbnailURL();
            },
            thumbnailLoaded: function() {
                this.loading = false;
            },
            // TODO: refactor
            parse: function() {
                const title = this.videoElement.querySelector("#video-title").textContent.trim();
                const info = parseInfoFromTitle(title);
                if (info === null)
                    return;
                this.number = info.number;
                this.subject = info.subject;
                this.topic = info.topic;
            },
            upload: async function() {
                if (this.template === null)
                    return;
                this.loading = true; // TODO: block form editing while waiting for upload

                const resp = await fetch("http://localhost:8888/thumbnail/upload", {
                    method: "POST",
                    body: JSON.stringify({
                        number: this.number,
                        topic: this.topic,
                        template: this.template,
                        fontSize: this.fontSize,
                        videoId: this.videoId,
                    }),
                });
                const respJson = await resp.json();
                console.log(respJson)

                this.loading = false; // TODO: block form editing while waiting for upload

                if (respJson !== null) {
                    alert(respJson["error"]);
                    return;
                }

                this.reloadYoutubeThumbnail();
            },
            reloadYoutubeThumbnail() {
                const ytThumbEl = this.videoElement.querySelector("#img");
                const ytThumbUrl = new URL(ytThumbEl.src);
                ytThumbUrl.searchParams.set("randomstring", `${Math.random()}`);
                ytThumbEl.src =  ytThumbUrl;
            }
        }
    });
}

async function main() {
    // cleanup existing widgets for hot reloading (during testing)
    document.querySelectorAll(".lt-container").forEach(el => el.remove())    

    const thumbnailerComponent = await createThumbnailerComponent();

    let avaliableTemplates = await (await fetch("http://localhost:8888/templates/list")).json();
    let exportsDict = await (await fetch("http://localhost:8888/exports/get")).json();

    // let avaliableTemplates = [];
    // let exportsDict = [];

    let videoElements = Array.from(document.getElementsByTagName("ytd-playlist-video-renderer"));
    thumbnailers = videoElements.map(videoEl => {
        const title = videoEl.querySelector("#video-title").textContent.trim();
        const contentEl = videoEl.querySelector("#content");
        const videoUrl = new URL(contentEl.querySelector(":scope > a").href);
        const videoId = videoUrl.searchParams.get("v");

        const info = {...parseInfoFromTitle(title), ...exportsDict[videoId]};

        let thumbnailer = new thumbnailerComponent({
            propsData: {
                ...info,
                videoElement: videoEl,
                avaliableTemplates: avaliableTemplates,
                videoId: videoId,
            }
        });

        const mountPoint = contentEl.appendChild(document.createElement("div"));
        thumbnailer.$mount(mountPoint);
        return thumbnailer;
    });
}



// async function maybeRebuildThumbnailers() {
//     console.log("123");
//     const oldURL = lastURL;
//     const newURL = lastURL = new URL(window.location);

//     if (newURL.pathname != "/playlist") {
//         //...
//     }

//     if (newURL.search != oldURL.search) {
//         // await sleep(300);
//         console.log("hi");
//         // main();
//     }
// }

// const maybeRebuildThumbnailersThrottled = maybeRebuildThumbnailers; //_.throttle(maybeRebuildThumbnailers, 100);

// var mutationObserver = new MutationObserver(() => maybeRebuildThumbnailersThrottled());

// let smt = document.getElementsByTagName("yt-page-navigation-progress")[0];
// console.log(">>>", smt);

// mutationObserver.observe(smt, {
//   attributes: true,
//   characterData: true,
//   childList: true,
//   subtree: true,
// });

main();