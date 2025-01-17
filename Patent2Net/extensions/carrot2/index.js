!function () {
    "use strict";
    var t, a = window.location, o = window.document, r = o.currentScript,
        s = r.getAttribute("data-api") || new URL(r.src).origin + "/api/event",
        l = window.localStorage.plausible_ignore;

    function w(t) {
        console.warn("Ignoring Event: " + t)
    }

    function e(t, e) {
        if (/^patent2net.uqam.ca$|^127(?:\.[0-9]+){0,2}\.[0-9]+$|^(?:0*\:)*?:?0*1$/.test(a.hostname) || "file:" === a.protocol) return w("patent2net.uqam.ca");
        if (!(window.phantom || window._phantom || window.__nightmare || window.navigator.webdriver || window.Cypress)) {
            if ("true" == l) return w("localStorage flag");
            var i = {};
            i.n = t, i.u = a.href, i.d = r.getAttribute("data-domain"), i.r = o.referrer || null, i.w = window.innerWidth, e && e.meta && (i.m = JSON.stringify(e.meta)), e && e.props && (i.p = JSON.stringify(e.props));
            var n = new XMLHttpRequest;
            n.open("POST", s, !0), n.setRequestHeader("Content-Type", "text/plain"), n.send(JSON.stringify(i)), n.onreadystatechange = function () {
                4 == n.readyState && e && e.callback && e.callback()
            }
        }
    }

    function i() {
        t !== a.pathname && (t = a.pathname, e("pageview"))
    }

    var n, p = window.history;
    p.pushState && (n = p.pushState, p.pushState = function () {
        n.apply(this, arguments), i()
    }, window.addEventListener("popstate", i));
    var d = window.plausible && window.plausible.q || [];
    window.plausible = e;
    for (var u = 0; u < d.length; u++) e.apply(this, d[u]);
    "prerender" === o.visibilityState ? o.addEventListener("visibilitychange", function () {
        t || "visible" !== o.visibilityState || i()
    }) : i()
}();
