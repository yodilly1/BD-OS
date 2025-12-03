import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Protect all routes except public ones
// We want to protect everything by default for an internal tool
const isPublicRoute = createRouteMatcher([
    "/sign-in(.*)",
    "/sign-up(.*)"
]);

export default clerkMiddleware(async (auth, req) => {
    if (!isPublicRoute(req)) {
        const { userId, redirectToSignIn } = await auth();
        if (!userId) {
            return redirectToSignIn();
        }
    }
});

export const config = {
    matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
};
