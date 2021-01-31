Structure
=========

.. graphviz::

   digraph foo {
      "svg file" -> "render_raytracing.Tracer" [label="add"];
      "render_raytracing.Tracer" -> "svg file";
   }
