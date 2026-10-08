// Gentle Shell 4 owns the NaN provider, authentication and model catalog.
// Preserve the original environment variable without registering a second
// provider or persisting credentials. Explicit NAN_API_KEY wins; native
// /login credentials retain the precedence established by Gentle Shell.
export default function () {
    if (!process.env.NAN_API_KEY && process.env.NAN_BUILDERS_API_KEY) {
        process.env.NAN_API_KEY = process.env.NAN_BUILDERS_API_KEY;
    }
}
