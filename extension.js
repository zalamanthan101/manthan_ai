// ============================================
// MANTHAN AI — VS Code Extension
// File: extension.js  (ROOT me rakho)
// ============================================

const vscode = require('vscode');
const { SidebarProvider } = require('./SidebarProvider');

function activate(context) {
    console.log('🔥 Manthan AI is now active!');

    // ── Sidebar Register ──────────────────────
    const sidebarProvider = new SidebarProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            "manthan-ai-sidebar",
            sidebarProvider
        )
    );

    // ── Helper: Selected code pakdo ───────────
    function getSelectedCode() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return "";
        return editor.document.getText(editor.selection);
    }

    // ── Command: Bug Fix ──────────────────────
    context.subscriptions.push(
        vscode.commands.registerCommand('manthan.fixBug', async () => {
            const code = getSelectedCode();
            if (!code) {
                vscode.window.showWarningMessage('Pehle code select karo, phir Fix karo!');
                return;
            }
            sidebarProvider.sendToChat('fix', `Fix this bug:\n\`\`\`\n${code}\n\`\`\``);
            vscode.commands.executeCommand('manthan-ai-sidebar.focus');
        })
    );

    // ── Command: Explain ──────────────────────
    context.subscriptions.push(
        vscode.commands.registerCommand('manthan.explain', async () => {
            const code = getSelectedCode();
            if (!code) {
                vscode.window.showWarningMessage('Pehle code select karo, phir Explain karo!');
                return;
            }
            sidebarProvider.sendToChat('explain', `Explain this code:\n\`\`\`\n${code}\n\`\`\``);
            vscode.commands.executeCommand('manthan-ai-sidebar.focus');
        })
    );

    // ── Command: Enhance ─────────────────────
    context.subscriptions.push(
        vscode.commands.registerCommand('manthan.enhance', async () => {
            const code = getSelectedCode();
            if (!code) {
                vscode.window.showWarningMessage('Pehle code select karo, phir Enhance karo!');
                return;
            }
            sidebarProvider.sendToChat('enhance', `Enhance and optimize this code:\n\`\`\`\n${code}\n\`\`\``);
            vscode.commands.executeCommand('manthan-ai-sidebar.focus');
        })
    );

    // ── Command: Open Chat ────────────────────
    context.subscriptions.push(
        vscode.commands.registerCommand('manthan.openChat', () => {
            vscode.commands.executeCommand('manthan-ai-sidebar.focus');
        })
    );

    vscode.window.showInformationMessage('🔥 Manthan AI Ready! Code select karo aur right-click karo.');
}

function deactivate() {}

module.exports = { activate, deactivate };