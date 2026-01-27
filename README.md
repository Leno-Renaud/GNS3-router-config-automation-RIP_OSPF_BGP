Projet GNS3 : ERNOULT Hector, RENAUD Leno, BONNIER Théodore, GRUFFAZ Jules

Ce projet est basé sur plusieurs scripts python ainsi que des templates jinja2.
Son objectif est d'automatiser la configuration de routeurs cisco c7200 dans un projet GNS3.
Son fonctionnement est garanti par son arborescence, ainsi, afin de l'utiliser, veuillez importer l'archive 'projet-gns' en entier.
Une fois ceci fait, il vous suffira d'exécuter le script python 'main.py' afin d'ouvrir l'interface graphique.
Celle-ci vous présentera un bref tutoriel d'utilisation, ce README va donc servir à apporter quelques précisions :

-> Ce projet fonctionne avec de nombreux imports (jinja2, tkinter...) : Veillez à les avoir installé avec 'pip install [import]'.

-> L'injection des configurations est automatisée via un système graphique : en utilisant le système de dessin de rectangles de GNS3, dessinez (en arrière plan, derrière vos routeurs) des rectangles encadrant vos
différentes AS. Un rectangle rouge pour RIP, un vert pour OSPF. A noter que le rectangle doit être 'purement' de la couleur voulue (exemple : RGB = 255, 0, 0) afin que le programme fonctionne.

-> Suite à des tests, il est à noter que la fonction de communities Gao-Rexford du programme est instable, et ne devra pas être utilisée si vous attendez un taux de réussite de 100%. 
Si cette case n'est pas cochée dans l'interface, le programme fonctionne parfaitement.

-> Notre programme propose une implémentation de métriques OSPF. Il est à noter qu'il est possible d'imposer une métrique OSPF à un lien entre deux routeurs RIP dans l'interface graphique.
Cependant, cela n'aura aucun effet sur les configurations finales.

-> Dernières précisions, le programme ne fonctionne que si les routeurs du projet GNS3 sont éteints lors de l'injection. 
De plus, l'exécution du programme écrasera toute configuration de startup présente dans la mémoire des routeurs auparavant.

Finalement, tout se fait via l'interface graphique. 
Vous devrez sélectionner votre projet GNS3 dans l'explorateur de fichier, puis une fois la fenêtre de succès apparue, vos routeurs sont configurés !
