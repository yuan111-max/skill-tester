function validateYAML(content) {
    try {
        const parsed = JSON.parse(JSON.stringify(content));
        return { valid: true, data: parsed };
    } catch (e) {
        return { valid: false, error: e.message };
    }
}

module.exports = { validateYAML };
