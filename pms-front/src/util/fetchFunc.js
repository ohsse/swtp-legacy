export async function fetchFunc(url, data){
    let options;
    if(data){
        options = {method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data)
        }
    }
    const res = await fetch(url, options);
    return await res.json();
}