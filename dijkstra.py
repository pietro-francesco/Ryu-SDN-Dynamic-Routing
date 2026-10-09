"""

dijkstra.py

Partendo dallo switch sorgente prova progressivamente tutte le strade disponibili, ricordandosi sempre il modo meno costoso trovato finora per
raggiungere ogni switch.

1. distances memorizza il costo minimo conosciuto per raggiungere ogni nodo dalla sorgente. La sorgente parte da 0, tutti gli altri da infinito.
2. unvisited contiene i nodi ancora da analizzare.
3. A ogni ciclo Dijkstra sceglie il nodo non visitato con il costo attualmente più basso.
4. Controlla i suoi vicini e calcola new_distance = distanza corrente + costo del link.
5. Se trova un percorso più economico, aggiorna distances e registra in previous da quale nodo è arrivato.
6. Raggiunta la destinazione, usa previous a ritroso per ricostruire il percorso e poi lo inverte.
"""

def dijkstra(graph, source, destination):
    
    # In distances memorizza qual è la migliore distanza che conosco attualmente da sorgente ad ogni nodo
    distances = {}
    # In previous memorizza da quale nodo sono arrivato per ottenere il percorso migliore
    previous = {}
    # Unvisited sono i nodi che Dijkstra deve ancora elaborare
    unvisited = set(graph.keys())

    # Inizializzazione
    for node in graph:
        distances[node] = float("inf")
        previous[node] = None

    distances[source] = 0

    # Fino a che ci sono nodi ancora da elaborare, continua
    while unvisited:
        # Cerca il nodo non visitato con distanza minima
        current = min(
            unvisited,
            key=lambda node: distances[node]
        )

        # Destinazione raggiunta o nodo non raggiungibile
        if current == destination or distances[current] == float("inf"):
            break

        unvisited.remove(current)

        # Guarda tutti i vicini del nodo corrente
        for neighbor, data in graph[current].items():
            cost = data["cost"]
            new_distance = distances[current] + cost
            
            # Se il vicino è ancora da elaborare e trovi un percorso migliore
            if neighbor in unvisited and new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current

    # Ricostruzione del percorso (fuori dal ciclo while)
    if distances[destination] == float("inf"):
        return None, float("inf")

    path = []
    current = destination

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()

    return path, distances[destination]

if __name__ == "__main__":
    graph = {
        1: {
            2: {"port": 2, "cost": 1},
            3: {"port": 3, "cost": 1}
        },
        2: {
            1: {"port": 1, "cost": 1},
            4: {"port": 2, "cost": 1}
        },
        3: {
            1: {"port": 1, "cost": 1},
            4: {"port": 2, "cost": 1}
        },
        4: {
            2: {"port": 1, "cost": 1},
            3: {"port": 2, "cost": 1},
            5: {"port": 3, "cost": 1}
        },
        5: {
            4: {"port": 2, "cost": 1}
        }
    }
    
    source = 1
    destination = 5
    
    path, cost = dijkstra(graph, source, destination)
    
    print("Sorgente:", source)
    print("Destinazione:", destination)
    print("Percorso minimo:", path)
    print("Costo totale:", cost)