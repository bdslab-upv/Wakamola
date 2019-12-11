/**
* @fileoverview Visualizador de graficos NetworkX mediante uso de libreria D3
* @version 1.4
* @author Wakamola
*/

// -----------------------------------------------------------------------------------------------
// ------------------------------- LIBRERIA D3 ---------------------------------------------------
// ----------------------------------(init)-------------------------------------------------------
// -----------------------------------------------------------------------------------------------

// Recuperamos del HTML el JSON con el grafo
var mis = document.getElementById('mis').innerHTML;
graph = JSON.parse(mis);
graph.comunidades = graph.links;
graphRec = JSON.parse(JSON.stringify(graph));

// Definimos el tamaño del area sobre la que crear el grafo
var width = window.innerWidth * 0.6;
var height = 650;

// Definimos una serie de constantes a utilizar despues
var padding_manu = 0;
var radio_nodo = 10;
var distancia_nodos = 3; // separacion entre nodos
var difuminado = 0.6;
var seleccionado = window.location.search

if (window.innerWidth < 500) {
  radio_nodo = 7;
  distancia_nodos = 10;
  padding_manu = 75;
  width = window.innerWidth -200;
}


var listado_vecinos = [];
var relaciones_entre_nodos = {};
var color_selected = "BMI";

// Creamos una instancia de layout de D3 sobre la que podemos configurar parametros de comportamiento de los nodos
var force = d3.layout.force()
.linkStrength(0.1)
.friction(0.9)
.linkDistance(20)
.charge(-40)
.gravity(0.05)
.theta(0)
.alpha(0)
.size([width, height]);

if (window.innerWidth < 500) {
  var force = d3.layout.force()
  .linkStrength(0.1)
  .friction(0.9)
  .linkDistance(5)
  .charge(-20)
  .gravity(0.05)
  .theta(0)
  .alpha(0)
  .size([width, height]);
}


// Creamos un objeto vectorial sobre el que pintar el grafo
var svg = d3.select("#graph-div").append("svg").attr("width", "100%").attr("height", height);
$(function() {  $("#neighbors").draggable();});

// Creamos los tips para cuando naveguemos por el grafo
// var tip = d3.tip().attr('class', 'd3-tip').offset([-10, 0]).html(function(d) {
//   // Le asignamos un tag
//   return Math.round(d.name) + "</span>";
// })
// svg.call(tip);

// Creamos en la instancia de D3 los nodos
force.nodes(graph.nodes).links(graph.links).start();

// Creamos en la instancia de D3 los arcos (sin posiciones)
var comunidades = svg.selectAll(".link2").data(graph.comunidades).enter().append("line").attr("class", "link2").style("stroke-width", function(d) {
  return 1;
});

var link = svg.selectAll(".link").data(graph.links).enter().append("line").attr("class", "link").style("stroke-width", function(d) {
  return 1;
});



// Damos formato a los nodos
var node = svg.selectAll(".node").data(graph.nodes).enter().append("g").attr("class", "gruponodo")

node.append("circle")
.attr("class", "nodeball").attr("r", radio_nodo)
.style("fill", function(d) {   return colorBMI(d.color) })
.call(force.drag)
.on('click', nodos_conectados)
// .on('mouseover', tip.show)
// .on('mouseout', tip.hide);

node.append("text")
.attr("class", "nodetext")
.text(function(d) { return Math.round(d.csv_BMI)})
.call(force.drag)
.on('click', nodos_conectados)
// .on('mouseover', tip.show)
// .on('mouseout', tip.hide);

// Ubicamos los nodos dentro del SVG
var node = svg.selectAll(".nodeball")
var nodetext = svg.selectAll(".nodetext")

force.on("tick", function() {
  link
  .attr("x1", function(d) { return d.source.x + padding_manu;})
  .attr("y1", function(d) { return d.source.y;})
  .attr("x2", function(d) { return d.target.x + padding_manu;})
  .attr("y2", function(d) { return d.target.y;});
  comunidades
  .attr("x1", function(d) { return d.source.x + padding_manu;})
  .attr("y1", function(d) { return d.source.y;})
  .attr("x2", function(d) { return d.target.x + padding_manu;})
  .attr("y2", function(d) { return d.target.y;});
  node
  .attr("cx", function(d) { return d.x + padding_manu; })
  .attr("cy", function(d) { return d.y;});
  nodetext
  .attr("x", function(d) { return d.x + padding_manu - 7.5;})
  .attr("y", function(d) { return d.y + 3.5;})
  node.each(collide(0.5));
});

// Función para definir el comportamiento de los choques en los renders
function collide(alpha) {
  var quadtree = d3.geom.quadtree(graph.nodes);
  return function(d) {
    var rb = 2 * radio_nodo + distancia_nodos,
    nx1 = d.x - rb,
    nx2 = d.x + rb,
    ny1 = d.y - rb,
    ny2 = d.y + rb;
    quadtree.visit(function(quad, x1, y1, x2, y2) {
      if (quad.point && (quad.point !== d)) {
        var x = d.x - quad.point.x,
        y = d.y - quad.point.y,
        l = Math.sqrt(x * x + y * y);
        if (l < rb) {
          l = (l - rb) / l * alpha;
          d.x -= x *= l;
          d.y -= y *= l;
          quad.point.x += x;
          quad.point.y += y;
        }
      }
      return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
    });
  };
}

// Marcar seleccionado
window.onload = function() {
  cambiarcolor()
  if(seleccionado){
    var seleccionado_aux = seleccionado.replace("?id=","")
    selected = node.filter(function(d, i) {     return d.id == seleccionado_aux;});
    not_selected = node.filter(function(d, i) { return d.id != seleccionado_aux;});
    not_selected.style("opacity", difuminado);
    selected.attr("r", 15)

    svg.selectAll(".link").style("opacity", difuminado);
    d3.selectAll(".node, .link").transition().duration(1000).attr("r", radio_nodo).style("opacity", 1);

    var lista_ordenada_wakastatus = []
    var lista_ordenada_p_ID_Variable = []
    for (var i = 0; i < graphRec.nodes.length; i++) {
      lista_ordenada_p_ID_Variable.push(graphRec.nodes[i].p_ID_Variable);
      lista_ordenada_wakastatus.push(graphRec.nodes[i].csv_wakaestado);
    }
    var seleccionado_id = lista_ordenada_p_ID_Variable.indexOf(seleccionado_aux)
    var seleccionado_ws = lista_ordenada_wakastatus[seleccionado_id]

    lista_ordenada_wakastatus.sort().reverse()
    var ranquing_ws = lista_ordenada_wakastatus.indexOf(seleccionado_ws)
    document.getElementById("ranquing_p").innerHTML = 'Tu wakastatus ocupa la posición ' + ranquing_ws + " de " +  lista_ordenada_wakastatus.length + " usuarios. Sigue mejorando tus habitos saludables para llegar a estar entre los 10 primeros"
    if(ranquing_ws <= 11){
      document.getElementById("ranquing_p").innerHTML = 'Tu wakastatus ocupa la posición ' + ranquing_ws + " de " +  lista_ordenada_wakastatus.length + " usuarios. Enhorabuena, ¡estas entre los 10 primeros!"
    }
    if(ranquing_ws <= -1){
      document.getElementById("ranquing_p").style.display = "none";
    }

  }else{
    document.getElementById("ranquing_p").style.display = "none";
    console.log("No se ha seleccionado ningun nodo en origen")
  }
};


// -----------------------------------------------------------------------------------------------
// ------------------------------- LIBRERIA D3 ---------------------------------------------------
// --------------------------------(buscador)-----------------------------------------------------
// -----------------------------------------------------------------------------------------------

// Preparamos un listado de valores unicos para el autocompletar
var opciones_buscadorBMI = [];
for (var i = 0; i < graph.nodes.length; i++) {
  var unico = "" + Math.round(graph.nodes[i].csv_BMI)
  if(!opciones_buscadorBMI.includes(unico)){
    opciones_buscadorBMI.push(unico);
  }
}
opciones_buscadorBMI = opciones_buscadorBMI.sort();

var opciones_buscadorWS = [];
for (var i = 0; i < graph.nodes.length; i++) {
  var unico = "" + Math.round(graph.nodes[i].csv_wakaestado)
  if(!opciones_buscadorWS.includes(unico)){
    opciones_buscadorWS.push(unico);
  }
}
opciones_buscadorWS = opciones_buscadorWS.sort();

// Asignamos dicho listado al buscador
$(function() { $("#search").autocomplete({  source: opciones_buscadorBMI });});

// Funcion de resaltado para valores seleccionados por el buscador
function searchNode() {

  // Encendemos todos los nodos y arcos
  var node = svg.selectAll(".nodeball").attr("r", radio_nodo).style("opacity", "1");
  var link = svg.selectAll(".link").style("opacity", "1");
  d3.selectAll(".node, .link").transition().duration(0).attr("r", radio_nodo).style("opacity", 1);

  // Tomamos el valor del buscador
  var search_value = document.getElementById('search').value.toString();

  var node = svg.selectAll(".nodeball");
  if(color_selected == "BMI"){
    selected = node.filter(function(d, i) {     return Math.round(d.csv_BMI) == search_value; });
    not_selected = node.filter(function(d, i) { return Math.round(d.csv_BMI) != search_value;});
  }else{
    selected = node.filter(function(d, i) {     return d.csv_wakaestado == search_value; });
    not_selected = node.filter(function(d, i) { return d.csv_wakaestado != search_value;});
  }

  //  Apagamos los nodos no seleccionados y resaltamos los seleccionados
  not_selected.style("opacity", difuminado);
  selected.attr("r", 15)

  // Apagamos todos los arcos
  svg.selectAll(".link").style("opacity", difuminado);
  d3.selectAll(".node, .link").transition().duration(1000).attr("r", radio_nodo).style("opacity", 1);
}


// -----------------------------------------------------------------------------------------------
// ------------------------------- LIBRERIA D3 ---------------------------------------------------
// --------------------------------(partitions)---------------------------------------------------
// -----------------------------------------------------------------------------------------------

// Función restart para devolver el grafo a su estado habitual
graph.comunidades =[]
function restart() {

  link = link.data(graph.links);
  link.exit().remove();
  link.enter().insert("line", ".node").attr("class", "link").style("stroke-width", 1);

  node = node.data(graph.nodes);
  node.enter().insert("circle", ".cursor").attr("class", "node").attr("r", radio_nodo).call(force.drag);
  force.start();

}

function particiones(thresh) {
  graph.comunidades = []
  graph.links.splice(0, graph.links.length);
  for (var i = 0; i < graphRec.links.length; i++) {
    var arco = graphRec.links[i];
    if (arco.value > thresh) {
      graph.links.push(arco);
    }
    else { if (thresh == 1) {
      graph.comunidades.push(arco);
    }
  }
}

restart();
}



// -----------------------------------------------------------------------------------------------
// ------------------------------- LIBRERIA D3 ---------------------------------------------------
// ---------------------------------(vecinos)-----------------------------------------------------
// -----------------------------------------------------------------------------------------------

// Función para modificar el texto con los datos de los vecinos
function texto_vecinos(listado_vecinos, seleccionado) {
  for (i = 0; i < listado_vecinos.length; i++) {
    izquierda = "ID_Node: " + seleccionado.id + " / "
    if (listado_vecinos[i].indexOf(izquierda) != 0) {
      var par = document.createElement('p');
      par.appendChild(document.createTextNode(listado_vecinos[i]));
      document.getElementById('inner_neighbors').appendChild(par);
    }
  }
  document.getElementById("select_title_p").innerHTML = seleccionado.texto_en

}


// Función para buscar vecinos
function neighboring(a, b) {
  relaciones_entre_nodos = []
  graph.links.forEach(function(d) {
    relaciones_entre_nodos[d.source.id + "," + d.target.id] = 1;
  });

  try {
    if (a.id != b.id) {
      if (relaciones_entre_nodos[a.id + "," + b.id]) {
        if ($.inArray(a.texto_en, listado_vecinos) == -1) { listado_vecinos.push(a.texto_en) }
        if ($.inArray(b.texto_en, listado_vecinos) == -1) { listado_vecinos.push(b.texto_en) }

      }
    }
    return relaciones_entre_nodos[a.id + "," + b.id];
  }
  catch(error) {}


}

//T Función cuando se clica en un nodo
var esta_seleccionado = 0;
function nodos_conectados() {
  if (esta_seleccionado == 0) {
    esta_seleccionado = 1;

    d = d3.select(this).node().__data__;

    listado_vecinos = []
    var node = svg.selectAll(".nodeball").attr("r", radio_nodo).style("opacity", "1");
    node.style("opacity", function(o) {     return neighboring(d, o) | neighboring(o, d) ? 1 : difuminado; });
    var link = svg.selectAll(".link").style("opacity", "1");
    link.style("opacity", function(o) {     return d.id == o.source.id | d.id == o.target.id ? 1 : difuminado; });

    selected = node.filter(function(o) { return o == d; });
    selected.style("opacity", 1);
    selected.attr("r", 15);
    texto_vecinos(listado_vecinos, d)

  } else {
    esta_seleccionado = 0;

    var node = svg.selectAll(".nodeball").attr("r", radio_nodo).style("opacity", "1");
    var link = svg.selectAll(".link").style("opacity", "1");
    d3.selectAll(".node").transition().duration(200).attr("r", radio_nodo)

    document.getElementById("select_title_p").innerHTML = 'Seleccione un nodo'
    document.getElementById("inner_neighbors").innerHTML = ''

  }
}


// -----------------------------------------------------------------------------------------------
// ------------------------------- COLORES -------------------------------------------------------
// -----------------------------------------------------------------------------------------------

// Color en función del BMI
function colorBMI(valor) {
  if (valor < 18.5) {    return "#ddf1fa" } // azul
  else if (valor < 25){  return "#a5cd86" } // verde
  else if (valor < 30){  return "#e5dc75" } // amarillo
  else {                 return "#F47E65" } // rojo
}

// Color en función del Wakastatus
function colorWS(valor) {
  if (valor >= 60){        return "#a5cd86" } // verde
  else if (valor > 30){   return "#e5dc75" } // amarillo
  else {                  return "#F47E65" } // rojo
}

// Color en función de escalado
function colorescalado(valor, vmin, vmax) {
  var escalado = 100 - ((valor-vmin)  * (100 / (vmax-vmin)))
  var r, g, b = 0;
  if(escalado < 50) {
    r = 255;
    g = Math.round(5.1 * escalado);
  }  else {
    g = 255;
    r = Math.round(510 - 5.1 * escalado);
  }
  var h = r * 0x10000 + g * 0x100 + b * 0x1;
  return '#' + ('000000' + h.toString(16)).slice(-6);
}

// Selector de escala de color
function cambiarcolor() {
  if(color_selected == "BMI"){
    color_selected = "WS"
    var node = svg.selectAll(".nodeball");
    var nodetext = svg.selectAll(".nodetext")
    // node.style("fill", function(d) { return colorescalado(d.csv_wakaestado, minWS, maxWS)})
    node.style("fill", function(d) { return colorWS(d.csv_wakaestado)})
    nodetext.text(function(d) { return d.csv_wakaestado});

    $(function() { $("#search").autocomplete({  source: opciones_buscadorWS });});

  }
  else {
    color_selected = "BMI"
    var node = svg.selectAll(".nodeball");
    var nodetext = svg.selectAll(".nodetext")
    node.style("fill", function(d) { return colorBMI(d.csv_BMI)})
    nodetext.text(function(d) { return Math.round(d.csv_BMI)});

    $(function() { $("#search").autocomplete({  source: opciones_buscadorBMI });});
  }
}


// -----------------------------------------------------------------------------------------------
// -------------------------------VALORES ESTADISTICOS--------------------------------------------
// -----------------------------------------------------------------------------------------------

var sample_size = graph.nodes.length

// Metodo para el calculo de la desviación tipica o estandar
function desviacion_tipica(values){
  var avg = average(values);
  var squareDiffs = values.map(function(value){
    var diff = value - avg;
    var sqrDiff = diff * diff;
    return sqrDiff;
  });
  var avgSquareDiff = average(squareDiffs);
  var stdDev = Math.sqrt(avgSquareDiff);
  return stdDev;
}

function average(data){
  var sum = data.reduce(function(sum, value){
    return sum + value;
  }, 0);
  var avg = sum / data.length;
  return avg;
}

// ---> Wakastatus
var minWS = 100
var maxWS = 0
var averageWS = 0
var arrayWS = []

for (var i = 0; i < graph.nodes.length; i++) {
  arrayWS.push(Math.round(graph.nodes[i].csv_wakaestado*10)/10);
  if(graph.nodes[i].csv_wakaestado > maxWS){ maxWS = Math.round(graph.nodes[i].csv_wakaestado)}
  if(graph.nodes[i].csv_wakaestado < minWS){ minWS = Math.round(graph.nodes[i].csv_wakaestado)}
  averageWS = averageWS  + Math.round(graph.nodes[i].csv_wakaestado)
}
averageWS = averageWS / sample_size
document.getElementById('minWS').innerHTML = Math.round(minWS);
document.getElementById('maxWS').innerHTML = Math.round(maxWS);
document.getElementById('averageWS').innerHTML = Math.round(averageWS*10)/10;
document.getElementById('standardesvWS').innerHTML = desviacion_tipica(arrayWS).toFixed(2);


// ---> IBM
var minBMI = 20
var maxBMI = 20
var averageBMI = 0
var arrayBMI = []

for (var i = 0; i < graph.nodes.length; i++) {
  arrayBMI.push(Math.round(graph.nodes[i].csv_BMI*10)/10);
  if(graph.nodes[i].csv_BMI > maxBMI){ maxBMI = Math.round(graph.nodes[i].csv_BMI*10)/10}
  if(graph.nodes[i].csv_BMI < minBMI){ minBMI = Math.round(graph.nodes[i].csv_BMI*10)/10}
  averageBMI = averageBMI + Math.round(graph.nodes[i].csv_BMI*10) /10
}
averageBMI = averageBMI / sample_size
document.getElementById('minBMI').innerHTML = Math.round(minBMI*10)/10;
document.getElementById('maxBMI').innerHTML = Math.round(maxBMI*10)/10;
document.getElementById('averageBMI').innerHTML = Math.round(averageBMI*10)/10;
document.getElementById('standardesvBMI').innerHTML = desviacion_tipica(arrayBMI).toFixed(2);


// ---> Diet
var minDiet = 100
var maxDiet = 0
var averageDiet = 0
var arrayDiet = []

for (var i = 0; i < graph.nodes.length; i++) {
  arrayDiet.push(Math.round(graph.nodes[i].csv_score_nutrition*10)/10);
  if(graph.nodes[i].csv_score_nutrition > maxDiet){ maxDiet = Math.round(graph.nodes[i].csv_score_nutrition*10)/10}
  if(graph.nodes[i].csv_score_nutrition < minDiet){ minDiet = Math.round(graph.nodes[i].csv_score_nutrition*10)/10}
  averageDiet = averageDiet + Math.round(graph.nodes[i].csv_score_nutrition*10) /10
}
averageDiet = averageDiet / sample_size
document.getElementById('minDiet').innerHTML = Math.round(minDiet*10)/10;
document.getElementById('maxDiet').innerHTML = Math.round(maxDiet*10)/10;
document.getElementById('averageDiet').innerHTML = Math.round(averageDiet*10)/10;
document.getElementById('standardesvDiet').innerHTML = desviacion_tipica(arrayDiet).toFixed(2);

// ---> Activity
var minActivity = 100
var maxActivity = 0
var averageActivity = 0
var arrayActivity = []

for (var i = 0; i < graph.nodes.length; i++) {
  arrayActivity.push(Math.round(graph.nodes[i].csv_score_activity*10)/10);
  if(graph.nodes[i].csv_score_activity > maxActivity){ maxActivity = Math.round(graph.nodes[i].csv_score_activity*10)/10}
  if(graph.nodes[i].csv_score_activity < minActivity){ minActivity = Math.round(graph.nodes[i].csv_score_activity*10)/10}
  averageActivity = averageActivity + Math.round(graph.nodes[i].csv_score_activity*10) /10
}
averageActivity = averageActivity / sample_size
document.getElementById('minActivity').innerHTML = Math.round(minActivity*10)/10;
document.getElementById('maxActivity').innerHTML = Math.round(maxActivity*10)/10;
document.getElementById('averageActivity').innerHTML = Math.round(averageActivity*10)/10;
document.getElementById('standardesvActivity').innerHTML = desviacion_tipica(arrayActivity).toFixed(2);

// ---> Social
var minSocial = 100
var maxSocial = 0
var averageSocial = 0
var arraySocial = []

for (var i = 0; i < graph.nodes.length; i++) {
  arraySocial.push(Math.round(graph.nodes[i].csv_score_social*10)/10);
  if(graph.nodes[i].csv_score_social > maxSocial){ maxSocial = Math.round(graph.nodes[i].csv_score_social*10)/10}
  if(graph.nodes[i].csv_score_social < minSocial){ minSocial = Math.round(graph.nodes[i].csv_score_social*10)/10}
  averageSocial = averageSocial + Math.round(graph.nodes[i].csv_score_social*10) /10
}
averageSocial = averageSocial / sample_size
document.getElementById('minSocial').innerHTML = Math.round(minSocial*10)/10;
document.getElementById('maxSocial').innerHTML = Math.round(maxSocial*10)/10;
document.getElementById('averageSocial').innerHTML = Math.round(averageSocial*10)/10;
document.getElementById('standardesvSocial').innerHTML = desviacion_tipica(arraySocial).toFixed(2);
