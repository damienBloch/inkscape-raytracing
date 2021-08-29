Structure
=========

.. graphviz::

   digraph foo {
      "svg file" -> "render_raytracing.Raytracing" [label="add"];
      "render_raytracing.Raytracing" -> "svg file";
   }
