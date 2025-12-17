import OpenAI from 'openai';
import type { AgentInputItem, Session } from '@openai/agents-core';
export type OpenAIConversationsSessionOptions = {
    conversationId?: string;
    client?: OpenAI;
    apiKey?: string;
    baseURL?: string;
    organization?: string;
    project?: string;
};
export declare function startOpenAIConversationsSession(client?: OpenAI): Promise<string>;
export declare class OpenAIConversationsSession implements Session {
    #private;
    constructor(options?: OpenAIConversationsSessionOptions);
    get sessionId(): string | undefined;
    getSessionId(): Promise<string>;
    getItems(limit?: number): Promise<AgentInputItem[]>;
    addItems(items: AgentInputItem[]): Promise<void>;
    popItem(): Promise<AgentInputItem | undefined>;
    clearSession(): Promise<void>;
}
