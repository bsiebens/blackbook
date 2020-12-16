<script>
    import { store } from "../stores/auth";

    let username = "";
    let password = "";

    function handleSubmit() {
        $store = { username };
    }
</script>

<div>
    <h1>Sign In</h1>
    <pre>{JSON.stringify($store, null, 2)}</pre>

    <form on:submit|preventDefault={handleSubmit}>
        <label> Username: </label>
        <input type="text" bind:value={username} placeholder="Username" />

        <label> Password: </label>
        <input type="password" bind:value={password} />

        <button type="submit">Submit</button>
    </form>
</div>
