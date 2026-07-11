// SPA Route mapping configuration pointing directly to our Flask endpoints
const routes = {
    "/": "/pages/home.html",
    "/about": "/pages/about.html",
    "/courses": "/pages/courses.html",
    "/gallery": "/pages/gallery.html",
    "/contact": "/pages/contact.html",
    "/admission": "/pages/admission.html"
};

const pageCache = {};

const navigateTo = async (url) => {
    history.pushState(null, null, url);
    await router();
};

const router = async () => {
    const path = window.location.pathname;
    const routePath = routes[path] || routes["/"];
    const appView = document.getElementById("app-view");

    if (pageCache[routePath]) {
        appView.innerHTML = pageCache[routePath];
    } else {
        try {
            const response = await fetch(routePath);
            if (!response.ok) throw new Error("Fragment not found");
            const html = await response.text();
            pageCache[routePath] = html;
            appView.innerHTML = html;
        } catch (error) {
            appView.innerHTML = `<div class="container text-center py-5"><h2>Navigation Error</h2><p>Could not fetch view portal content.</p></div>`;
        }
    }

    window.scrollTo({ top: 0, behavior: "smooth" });

    // Handle mobile navbar toggle automatic collapse on action execution
    const navbarCollapse = document.getElementById('navbarNav');
    if (navbarCollapse && navbarCollapse.classList.contains('show')) {
        const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
        if (bsCollapse) bsCollapse.hide();
    }

    // Refresh layout view animation registers dynamically
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 1000, once: true });
    }
};

document.addEventListener("DOMContentLoaded", () => {
    document.body.addEventListener("click", e => {
        const link = e.target.closest("[data-link]");
        if (link) {
            e.preventDefault();
            navigateTo(link.getAttribute("href"));
        }
    });
    router();
});

window.addEventListener("popstate", router);