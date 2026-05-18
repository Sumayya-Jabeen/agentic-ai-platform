import { redirect } from "next/navigation";

// Root page — redirect straight to the chat
export default function Home() {
  redirect("/chat");
}
